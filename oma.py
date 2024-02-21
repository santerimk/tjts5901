#!/usr/bin/python
# -*- coding: utf-8 -*-

from flask import Flask, session, redirect, url_for, escape, request, Response, render_template, flash
import hashlib
import sys
from functools import wraps
import sqlite3
import os
import werkzeug.exceptions
from connection import toteuta
from polyglot import PolyglotForm
from wtforms import Form, BooleanField, StringField, validators, IntegerField, SelectField, widgets, SelectMultipleField, ValidationError, PasswordField, SubmitField, RadioField, FieldList
import json
from flask_wtf.csrf import CSRFProtect

from dotenv import load_dotenv
load_dotenv()
app = Flask(__name__)
app.config.update(
    SESSION_COOKIE_SAMESITE='Lax'
)
app.secret_key = b'\xc5\x8b\x9d\xb2\x96\xf6\xc3;\x12\x1c.gq!\xfb\xc5\xa5\xa3TR\xc8xhz' # Salainen avain CSRF-suojausta varten.
csrf = CSRFProtect(app) # Lisätään flask-sovellukseen CSRF-suojaus (Cross-site request forgery).
csrf.init_app(app) # Alustetaan CSRF-suojaus.
# WTF_CSRF_CHECK_DEFAULT = False // JOS TARVITSEE POISTAA KÄYTÖSTÄ CSRF-SUOJAUS!




# ========== TAVALLINEN KÄYTTÄJÄ ==========


def auth(f):
    """ Tämä decorator hoitaa tavallisen käyttäjän kirjautumisen tarkistamisen ja ohjaa tarvittaessa kirjautumissivulle.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        # Tarkistetaan onko kirjautumistarksitusmuuttuja asetettu.
        if not 'kirjautunut' in session:
            # Jos ei, palataan takaisin kirjautumissivulle.
            return redirect(url_for('kirjaudu'))
        return f(*args, **kwargs)
    return decorated


@app.route('/')
def paaikkuna():
    """ Ohjaa tavallisen käyttäjän kirjautumissivulle.
    """
    return redirect(url_for("kirjaudu"))


@app.route('/kirjaudu', methods=['POST','GET'])
def kirjaudu():
    """ Luo, käsittelee ja hoitaa tavallisen käyttäjän kirjautumisen.
    """
    kilpailu_id = request.form.get('kilpailu', 0)
    joukkue_nimi = request.form.get("joukkue", "").strip().lower()
    joukkue_salasana = request.form.get('salasana', "")
    # Haetaan tietokannasta jokaisen kilpailun tarpeellinen data.
    queryData_kaikkiKilpailut = toteuta("""
        SELECT id, kisanimi, YEAR(alkuaika) AS vuosi
        FROM kilpailut
    """)
    kilpailut = [(None, "--Valitse kilpailu--")]
    for kilpailu in queryData_kaikkiKilpailut:
        kilpailut.append((kilpailu["id"], f"{kilpailu['kisanimi']} {kilpailu['vuosi']}"))

    class Kirjautuminen(PolyglotForm):
        """ Luokka generoimaan tavallisen käyttäjän kirjautumislomakkeen."""
        kilpailu = SelectField("Kilpailu", choices=kilpailut, default="--Valitse kilpailu--")
        joukkue = StringField("Joukkue", default="", validators=[validators.InputRequired()])
        salasana = PasswordField("Salasana", default="", validators=[validators.InputRequired()])
        kirjaudu = SubmitField("Kirjaudu sisään", )

    # Luodaan kirjautumislomakkeen instanssi.
    lomake = Kirjautuminen()
    # Haetaan valitun kilpailun tarkemmat tiedot.
    queryData_valittuKilpailu = toteuta("""
        SELECT id, kisanimi, YEAR(alkuaika) as vv, MONTH(alkuaika) as kk, DAY(alkuaika) as pp
        FROM kilpailut
        WHERE id = %s
    """, parametrit=(kilpailu_id,), yksi=True)
    try:
        # Haetaan syötetyn joukkueen tiedot, jos hakusanalla löytyy.
        queryData_valittuJoukkue = toteuta("""
            SELECT j.joukkuenimi, j.id, j.salasana, j.jasenet, j.sarja
            FROM joukkueet j, sarjat s, kilpailut k
            WHERE joukkuenimi = %s
            AND s.id = j.sarja
            AND k.id = s.kilpailu
            AND k.id = %s
        """, parametrit=(joukkue_nimi, queryData_valittuKilpailu["id"]), yksi=True)
        if queryData_valittuJoukkue["id"] and queryData_valittuJoukkue["salasana"]:
            pass
    except TypeError or KeyError:
        # Käsitellään epäonnistunut kirjautuminen
        if 0 < len(joukkue_nimi) or 0 < len(joukkue_salasana):
            flash("Kirjautuminen epäonnistui.", "error")
        return render_template('kirjaudu.html', lomake=lomake)
    # Lähdetään tarkastamaan salasanaa vasta, kun ollaan varmistuttu, että syötetty joukkue löytyy valitusta kilpailusta.
    m = hashlib.sha512() # Luodaan heksadesimaali generaattori.
    m.update(str(queryData_valittuJoukkue["id"]).encode("UTF-8")) # Lisätään joukkueen id etuliitteksi turvaamaan varsinainen salasana.
    m.update(joukkue_salasana.encode("UTF-8")) # Lisätään sitten varsinainen salasana.
    # Verrataan syötetyn salasanan heksageneroitua merkkijonoa valitun joukkueen salasanaan.
    if m.hexdigest() == queryData_valittuJoukkue["salasana"]:
        # Jos täsmäävät keskenään, alustetaan sessio valitun kilpailun, sarjan ja joukkueen tiedoilla.
        # Asetetaan samalla kirjautumistarkistusmuuttujaan arvo.
        session.clear()
        session["kirjautunut"] = "ok"
        session["kilpailu"] = {"id": kilpailu_id, "nimi": queryData_valittuKilpailu["kisanimi"], "aika": f"{queryData_valittuKilpailu['vv']:02d}-{queryData_valittuKilpailu['kk']:02d}-{queryData_valittuKilpailu['pp']:02d}"}
        session["joukkue"] = {"id": queryData_valittuJoukkue["id"], "nimi": queryData_valittuJoukkue["joukkuenimi"], "salasana": queryData_valittuJoukkue["salasana"], "sarja": queryData_valittuJoukkue["sarja"]}
        session["jasenet"] = json.loads(queryData_valittuJoukkue["jasenet"])
        session["sarja"] = toteuta("""
            SELECT id, sarjanimi AS nimi
            FROM sarjat
            WHERE id = %s
        """, parametrit=(queryData_valittuJoukkue["sarja"],), yksi=True)
        # Ohjataan listaussivun käsitellijälle.
        return redirect(url_for('listaus'))
    # Jos taas salasana on väärä, ilmoitetaan virheestä ja ohjataan takaisin kirjautumiseen.
    flash("Kirjautuminen epäonnistui.", "error")
    return render_template('kirjaudu.html', lomake=lomake)


@app.route('/listaus', methods=['POST','GET'])
@auth
def listaus():
    """ Hakee kilpailun sarjojen sisällöt ja avaa sivun, jolla kyseiset tiedot listataan.
    """
    queryData = toteuta("""
        SELECT s.sarjanimi AS sarja, j.joukkuenimi AS joukkue, j.jasenet AS jasenet
        FROM sarjat s, joukkueet j
        WHERE s.id = j.sarja
        AND s.kilpailu = %s
        ORDER BY s.sarjanimi ASC, j.joukkuenimi ASC
    """, parametrit=(session["kilpailu"]["id"],))
    # Valmistellaan HTML-dokumentille välitettävä Jinja2 muuttuja siten, että se on helppo purkaa silmukalla.
    # Muuttujan rakenne on: sarjat(dict) -> joukkueet(dict) -> jäsenet(array) -> jäsen(string).
    kilpailunSarjat = {}
    for rivi in queryData:
        try:
            sarja = rivi["sarja"]
            joukkue = rivi["joukkue"]
            jasenet = json.loads(rivi["jasenet"])
            jasenet.sort(key=lambda jasen:
                jasen.lower().strip())
        except KeyError:
            continue
        if sarja not in kilpailunSarjat:
            kilpailunSarjat[sarja] = {}
        kilpailunSarjat[sarja][joukkue] = jasenet
    # Avataan valitun kilpailun sarjojen listaussivu.
    return render_template('listaus.html', kilpailunSarjat=kilpailunSarjat)


class JoukkueMuokkaus(PolyglotForm):
    """ Luokka generoimaan tavallisen käyttäjän joukkueen muokkaamislomakkeen.
    """
    def __init__(self, formdata=None, sarjat=[], sarja_id=-1, **kwargs):
        super().__init__(formdata, **kwargs)
        self.sarja_id = sarja_id # Lisätään valitun sarjan id attribuutiksi.
        self.sarja.choices = sarjat # Asetetaan sarjat parametri vaihtotehdoiksi SelectFieldille.
        # Otetaan jo olemassa olevien jäsenkenttien sisältö tilapäiseen temp-muuttujaan.
        temp = self.jasenet.data
        # Poistetaan FieldListin kaikki jäsenkentät (StringField).
        while self.jasenet.data:
            self.jasenet.pop_entry()
        # Täytetään FieldList uudestaan niillä jäsenkentillä, joissa oli jotakin sisältöä temp-muuttujan arvoja hyödyntäen.
        i = 1
        for jasen in temp:
            if jasen.strip():
                self.jasenet.append_entry(jasen)
                self.jasenet[-1].label = f"Jäsen {i}"
                i += 1
        # Lisätään täytettyjen kenttien perään vielä yksi tyhjä jäsenkenttä mahdollista uutta jäsentä varten.
        self.jasenet.append_entry("")
        self.jasenet[-1].label = f"Jäsen {i}"
        i += 1
        # Tarkistetaan, että vähintään kaksi jäsenkenttää löytyy ja lisätään vielä toinen tarvittaessa.
        if len(self.jasenet) < 2:
            self.jasenet.append_entry("")
            self.jasenet[-1].label = f"Jäsen {i}"
    
    def joukkueenNimi():
        """ Validaattori joukkueen nimisyötteelle.
        """
        def _joukkueenNimi(self, field):
            # Tarkistetaan onko joukkuekentässä sisältöä.
            onkoTaytetty = field.data and len(field.data.strip()) or 0
            if not onkoTaytetty:
                # Jos ei, asetetaan validointivirhe.
                raise ValidationError(f"Joukkue tarvitsee nimen.")
            # Tarkistetaan onko syötetty nimi jo jonkin muun kuin muokattavan joukkueen käytössä.
            syotettyNimi = field.data.lower().strip()
            aiempiNimi = session["joukkue"]["nimi"].lower().strip()
            if syotettyNimi == aiempiNimi:
                return
            joukkueet = toteuta("""
                SELECT joukkuenimi AS nimi
                FROM joukkueet
                WHERE sarja = %s
            """, parametrit=(self.sarja_id,))
            for joukkue in joukkueet:
                verrattavaNimi = joukkue["nimi"].lower().strip()
                if syotettyNimi == verrattavaNimi:
                    # Jos on, asetetaan validointivirhe.
                    raise ValidationError(f'Joukkueen nimi "{field.data}" on jo käytössä.')
        return _joukkueenNimi

    def jasenkenttienNimet():
        """ Validaattori joukkueen jäsensyötteille.
        """
        def _jasenkenttienNimet(self, field):
            # Haetaan ne jäsenkentät, joissa on jotakin sisältöä.
            oikeat_jasenet = [jasen.lower().strip() for jasen in self.jasenet.data if jasen.strip()]
            if len(oikeat_jasenet) < 2:
                # Jos sisällöllisiä kenttiä vähemmän kuin kaksi, asetetaan validointivirhe.
                raise ValidationError(f"Joukkueella on oltava vähintään kaksi jäsentä.")
            # Tarkistetaan onko jokaisen jäsenkentän sisältö ainutlaatuinen.
            ovatko_nimet_ainutlaatuisia = len(oikeat_jasenet) == len(set(oikeat_jasenet))
            if not ovatko_nimet_ainutlaatuisia:
                # Jos ei ole, asetetaan validointivirhe.
                raise ValidationError(f"Joukkueen jäsenillä ei saa olla samoja nimiä.")
        return _jasenkenttienNimet

    # Luodaan lomakkeen sisältö.
    nimi = StringField("Joukkueen nimi", validators=[joukkueenNimi()])
    salasana = PasswordField("Salasana", default="")
    sarja = SelectField("Sarja", validators=[validators.InputRequired()])
    jasenet = FieldList(StringField(validators=[jasenkenttienNimet()]))
    lisays = SubmitField("Alusta tyhjä", default="uusi")
    tallennus = SubmitField("Tallenna", default="tallenna")


@app.route('/joukkue_muokkaus', methods=['POST','GET'])
@auth
def joukkue_muokkaus():
    """ Hakee tiedot joukkueesta, jonka tiedoilla on kirjauduttu sisään ja esitäyttää muokkauslomakkeen kyseisen joukkueen datalla.
    Avaa näkymän, jossa käyttäjä voi muokata joukkueensa tietoja.
    """
    queryData = toteuta("""
        SELECT s.id, s.sarjanimi
        FROM sarjat s, kilpailut k
        WHERE s.kilpailu = %s
        GROUP BY s.id, s.sarjanimi
        ORDER BY s.sarjanimi ASC
    """, parametrit=(session["kilpailu"]["id"],))
    sarjat = []
    for sarja in queryData:
        sarjat.append((sarja["id"], sarja["sarjanimi"]))
    session["kilpailu"]["sarjat"] = sarjat
    # Luodaan instanssi joukkueen muokkauslomakkeesta ja avataan joukkueen muokkaussivu.
    lomake = JoukkueMuokkaus(sarjat=session["kilpailu"]["sarjat"], sarja=session['joukkue']["sarja"], nimi=session['joukkue']["nimi"], jasenet=session["jasenet"], sarja_id=session["sarja"]["id"])
    return render_template('joukkue_muokkaus.html', lomake=lomake)


@app.route('/tallenna_joukkue', methods=['POST'])
@auth
def tallenna_joukkue():
    """ Hoitaa joukkueen muokkauslomkkeen validoinnin ja sen läpäistessään myös joukkueeseen tehtyjen muutosten tallentamisen.
    Käsittelee uusien jäsenkenttien lisäämisen, jos on painettu "Alusta tyhjä" painiketta.
    """
    lomake = JoukkueMuokkaus(request.form, sarjat=session["kilpailu"]["sarjat"], sarja_id=session["sarja"]["id"])
    # Tarkistetaan painettiinko "Alusta tyhjä"-painiketta,
    if request.form.get("lisays", ""):
        # Jos painettiin, avataan sama joukkueen muokkausnäkymä alustetulla jäsenkentällä uudelleen.
        return render_template('joukkue_muokkaus.html', lomake=lomake)
    # Muussa tapauksessa jatketaan joukkueen tallentamiseen.
    id = session["joukkue"]["id"] # Käytetään joukkueen jo olemassa olevaa id:tä.
    nimi = lomake.nimi.data # Haetaan syötetty nimi lomakkeesta.
    salasana = generoiSalasana(id, lomake.salasana.data) # Generoidaan uusi salasana lomakkeeseen syötetyn merkkijonon perusteella.
    sarja = lomake.sarja.data # Haetaan valittu sarja lomakkeesta.
    jasenet = []
    # Haetaan syötetyt jäsenet lomakkeesta.
    for jasen in lomake.jasenet.data:
        if jasen.strip():
            jasenet.append(jasen)
    # Validoidaan lomake.
    if not lomake.validate():
        # Jos validointia ei läpäistä, palataan takaisin joukkueen muokkausnäkymään tallentamatta muutoksia.
        return render_template('joukkue_muokkaus.html', lomake=lomake)
    # Jos validointi läpäistään, päivitetään joukkueen tiedot tietokantaan.
    toteuta("""
        UPDATE joukkueet
        SET joukkuenimi = %s, salasana = %s, sarja = %s, jasenet = %s
        WHERE id = %s
    """, parametrit=(nimi, salasana, sarja, json.dumps(jasenet), id), hae=False)
    # Tallennetaan myös muuttuneet tiedot sessiomuuttujiin.
    session["joukkue"]["nimi"] = nimi
    session["joukkue"]["salasana"] = salasana
    session["joukkue"]["sarja"] = sarja
    session["jasenet"] = jasenet
    # Avataan lopuksi joukkueen muokkausnäkymä uudelleen.
    return redirect(url_for("joukkue_muokkaus"))


@app.route('/logout')
def logout():
    """ Hoitaa tavallisen käyttäjän uloskirjaamisen tyhjentämällä sessiomuuttujat ja ohjaamalla takaisin kirjautumissivulle.
    """
    # Vaihtoehtoinen tapa tyhjentää: [session.pop(key) for key in list(session.keys())]
    session.clear()
    return redirect(url_for('kirjaudu'))




# ========== ADMIN KÄYTTÄJÄ ==========


def admin_auth(f):
    """ Tämä decorator hoitaa admin käyttäjän kirjautumisen tarkistamisen ja ohjaa tarvittaessa kirjautumissivulle.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        # Tarkistetaan onko adminin kirjautumistarksitusmuuttuja asetettu.
        if not 'admin_kirjautunut' in session:
            # Jos ei, palataan takaisin adminin kirjautumissivulle.
            return redirect(url_for('admin_kirjaudu'))
        return f(*args, **kwargs)
    return decorated


@app.route('/admin')
def admin_paaikkuna():
    """ Ohjaa admin käyttäjän kirjautumissivulle.
    """
    return redirect(url_for("admin_kirjaudu"))


@app.route('/admin_kirjaudu', methods=['POST','GET'])
def admin_kirjaudu():
    """ Luo, käsittelee ja hoitaa admin käyttäjän kirjautumisen.
    """
    tunnus = request.form.get("tunnus", "").strip().lower()
    salasana = request.form.get('salasana', "")

    class AdminKirjautuminen(PolyglotForm):
        """ Luokka generoimaan admin käyttäjän kirjautumislomakkeen."""
        tunnus = StringField("Tunnus", default="", validators=[validators.InputRequired()])
        salasana = PasswordField("Salasana", default="", validators=[validators.InputRequired()])
        kirjaudu = SubmitField("Kirjaudu sisään", )

    # Luodaan kirjautumislomakkeen instanssi.
    lomake = AdminKirjautuminen()
    # Tarkistetaan täsmäävätkö syötetyn salasanan heksageneroitu merkkijono vaaditun kanssa keskenään.
    m = hashlib.sha512() # Luodaan heksadesimaali generaattori.
    m.update("salasala".encode("UTF-8")) # Lisätään jokin valittu etuliite turvaamaan varsinainen salasana.
    m.update(salasana.encode("UTF-8")) # Lisätään sitten varsinainen salasana.
    if tunnus == "admin"and m.hexdigest() == "994e78d502e245a69016332445d6bfd295c49df159ac82d31e419a3d83130348f4c02e1f34a8cd32a767e0c400a34da85f2f4cca817b72d291c8dae259400808":
        # Jos täsmäävät, alustetaan sessio kaikilla tietokannasta löytyvillä kilpailuilla.
        # Asetetaan myös adminin kirjautumistarkistusmuuttujaan arvo.
        session.clear()
        session['admin_kirjautunut'] = "ok"
        session["kilpailut"] = toteuta("""
            SELECT id, kisanimi, YEAR(alkuaika) as vv, MONTH(alkuaika) as kk, DAY(alkuaika) as pp
            FROM kilpailut
            ORDER BY vv ASC
        """)
        # Ohjataan kilpailulistaussivun käsittelijälle.
        return redirect(url_for('admin_kilpailut'))
    # Jos salasana on väärä, ilmoitetaan virheestä ja ohjataan takaisin kirjautumiseen.
    if 0 < len(tunnus) or 0 < len(salasana):
        flash ("Kirjautuminen epäonnistui.", "error")
    return render_template('admin_kirjaudu.html', lomake=lomake)


@app.route('/admin_kilpailut', methods=['POST','GET'])
@admin_auth
def admin_kilpailut():
    """ Avaa kilpailujen listaussivun tai kilpailujen puuttuessa ohjaa takaisin adminin pääsivulle.
    """
    try:
        # Tarkistetaan löytyykö sessiosta kilpailuja.
        if session["kilpailut"]:
            pass
    except KeyError:
        # Jos ei, ohjataan takaisin adminin kirjautumissivulle.
        return redirect(url_for("admin"))
    kilpailut = []
    for kilpailu in session["kilpailut"]:
        kilpailut.append({"id": kilpailu["id"], "nimi": kilpailu["kisanimi"], "aika": f"{kilpailu['vv']:02d}-{kilpailu['kk']:02d}-{kilpailu['pp']:02d}"})
    # Avataan kilpailulistaussivu.
    return render_template('admin_kilpailut.html', kilpailut=kilpailut)


@app.route('/admin_sarjat', methods=['POST','GET'])
@admin_auth
def admin_sarjat():
    """ Avaa valitun kilpailun sarjojen listaussivun tai niiden puuttuessa ohjaa takaisin kilpailulistaussivulle.
    """
    # Haetaan polun parametreistä "kilpailu":n arvo.
    kilpailu_id = request.args.get("kilpailu", "")
    if kilpailu_id:
        # Jos löytyy, nollataan session mahdolliset sarja ja joukkue -muuttujat.
        nollaa_sarja()
        nollaa_joukkue()
        try:
            # Haetaan parametriä vastaavan kilpailun tiedot ja asetetaan (muokattuna) session kilpailuksi.
            queryData = toteuta("""
                SELECT id, kisanimi AS nimi, YEAR(alkuaika) AS vv, MONTH(alkuaika) AS kk, DAY(alkuaika) AS pp
                FROM kilpailut
                WHERE id = %s
            """, parametrit=(kilpailu_id,), yksi=True)
            session["kilpailu"] = {"id": queryData["id"], "nimi": queryData["nimi"], "aika": f"{queryData['vv']:02d}-{queryData['kk']:02d}-{queryData['pp']:02d}"}
        except TypeError:
            # Jos annettu parametri oli huono, palataan takaisin kilpailulistaussivulle ja ilmoitetaan virheestä.
            flash("Haettua kilpailua ei löytynyt!", "search")
            return redirect(url_for("admin_kilpailut"))
    else:
        try:
            # Jos kilpailu parametriä ei löydy, käytetään session nykyistä kilpailua.
            kilpailu_id = session["kilpailu"]["id"]
        except KeyError:
            # Jos sellaistakaan ei ole, palataan takaisin kilpailulistaussivulle.
            return redirect(url_for("admin_kilpailut"))
    try:
        # Haetaan valitun kilpailun id:n perusteella tietokannasta kaikki kyseisen kilpailun sarjat.
        session["sarjat"] = toteuta("""
            SELECT s.id, s.sarjanimi
            FROM sarjat s, kilpailut k
            WHERE s.kilpailu = k.id
            AND k.id = %s
        """, parametrit=(kilpailu_id,))
        if not session["sarjat"]:
            # Jos haun perusteella ei saada yhtään sarjaa, palataan takaisin kilpailulistaussivulle.
            return redirect(url_for("admin_kilpailut"))
        sarjat = []
        for sarja in session["sarjat"]:
            sarjat.append({"id": sarja["id"], "nimi": sarja["sarjanimi"]})
    except KeyError:
        # Myös muiden sessiomuuttujan avainvirheiden tapahtuessa palataan takaisin kilpailulistaussivulle.
        return redirect(url_for("admin_kilpailut"))
    # Avataan sarjalistaussivu.
    return render_template('admin_sarjat.html', sarjat=sarjat)


class Admin_JoukkueLuonti(PolyglotForm):
    """ Luokka generoimaan joukkueen luontilomakkeen.
    """
    def __init__(self, formdata=None, sarja_id=-1, **kwargs):
        super().__init__(formdata, **kwargs)
        self.sarja_id = sarja_id # Lisätään valitun sarjan id attribuutiksi.
        # Otetaan jo olemassa olevien jäsenkenttien sisältö tilapäiseen temp-muuttujaan.
        temp = self.jasenet.data
        # Poistetaan FieldListin kaikki jäsenkentät (StringField)
        while self.jasenet.data:
            self.jasenet.pop_entry()
        # Täytetään FieldList uudestaan niillä jäsenkentillä, joissa oli jotakin sisältöä temp-muutujan arvoja hyödyntäen.
        i = 1
        for jasen in temp:
            if jasen.strip():
                self.jasenet.append_entry(jasen)
                self.jasenet[-1].label = f"Jäsen {i}"
                i += 1
        # Lisätään täytettyjen kenttien perään vielä yksi tyhjä jäsenkenttä mahdollista uutta jäsentä varten.
        self.jasenet.append_entry("")
        self.jasenet[-1].label = f"Jäsen {i}"
        i += 1
        # Tarkistetaan, että vähintään kaksi jäsenkenttää löytyy ja lisätään vielä toinen tarvittaessa.
        if len(self.jasenet) < 2:
            self.jasenet.append_entry("")
            self.jasenet[-1].label = f"Jäsen {i}"
    
    def joukkueenNimi():
        """ Validaattori joukkueen nimisyötteelle.
        """
        def _joukkueenNimi(self, field):
            # Tarkistetaan onko joukkuekentässä sisältöä.
            onkoTaytetty = field.data and len(field.data.strip()) or 0
            if not onkoTaytetty:
                # Jos ei, asetetaan validointivirhe.
                raise ValidationError(f"Joukkue tarvitsee nimen.")
            # Tarkistetaan onko syötetty nimi jo jonkin joukkueen käytössä.
            syotettyNimi = field.data.lower().strip()
            joukkueet = toteuta("""
                SELECT joukkuenimi AS nimi
                FROM joukkueet
                WHERE sarja = %s
            """, parametrit=(self.sarja_id,))
            for joukkue in joukkueet:
                verrattavaNimi = joukkue["nimi"].lower().strip()
                if syotettyNimi == verrattavaNimi:
                    # Jos on, asetetaan validointivirhe.
                    raise ValidationError(f'Joukkueen nimi "{field.data}" on jo käytössä.')
        return _joukkueenNimi

    def jasenkenttienNimet():
        """ Validaattori joukkueen jäsensyötteille.
        """
        def _jasenkenttienNimet(self, field):
            # Haetaan ne jäsenkentät, joissa on jotakin sisältöä.
            oikeat_jasenet = [jasen.lower().strip() for jasen in self.jasenet.data if jasen.strip()]
            if len(oikeat_jasenet) < 2:
                # Jos sisällöllisiä kenttiä on vähemmän kuin kaksi, asetetaan validointivirhe.
                raise ValidationError(f"Joukkueella on oltava vähintään kaksi jäsentä.")
            # Tarkistetaan onko jokaisen jäsenkentän sisältö aintulaatuinen.
            ovatko_nimet_ainutlaatuisia = len(oikeat_jasenet) == len(set(oikeat_jasenet))
            if not ovatko_nimet_ainutlaatuisia:
                # Jos ei ole, asetetaan validointivirhe.
                raise ValidationError(f"Joukkueen jäsenillä ei saa olla samoja nimiä.")
        return _jasenkenttienNimet

    # Luodaan lomakkeen sisältö.
    nimi = StringField("Joukkueen nimi", validators=[joukkueenNimi()])
    salasana = PasswordField("Salasana", default="")
    jasenet = FieldList(StringField(validators=[jasenkenttienNimet()]))
    lisays = SubmitField("Alusta tyhjä", default="uusi")
    poisto = BooleanField("Poista joukkue", default=False)
    tallennus = SubmitField("Tallenna", default="tallenna")


@app.route('/admin_joukkueet', methods=['POST','GET'])
@admin_auth
def admin_joukkueet():
    """ Avaa valitun sarjan joukkueiden listaussivun tai niiden puuttuessa ohjaa takaisin sarjalistaussivulle.
    Avaa myös näkymän, jossa käyttäjä voi luoda uuden joukkueen.
    """
    # Haetaan polun parametreistä "sarja":n arvo.
    sarja_id = request.args.get("sarja", "")
    if sarja_id:
        # Jos löytyy, nollataan session mahdollinen joukkue -muuttuja.
        nollaa_joukkue()
        # Haetaan parametriä vastaavan sarjan tiedot ja asetetaan session sarjaksi.
        try:
            queryData = toteuta("""
                SELECT id, sarjanimi AS nimi
                FROM sarjat
                WHERE id = %s
            """, parametrit=(sarja_id,), yksi=True)
            session["sarja"] = {"id": queryData["id"], "nimi": queryData["nimi"]}
        except TypeError:
            # Jos annettu parametri oli huono, palataan takaisin sarjalistaussivulle ja ilmoitetaan virheestä.
            flash("Haettua sarjaa ei löytynyt!", "search")
            return redirect(url_for("admin_sarjat"))
    else:
        try:
            # Jos sarja parametriä ei löydy, käytetään session nykyistä sarjaa.
            sarja_id = session["sarja"]["id"]
        except KeyError:
            # Jos sitäkään ei ole, palataan takaisin sarjalistaussivulle.
            return redirect(url_for("admin_sarjat"))
    try:
        session["joukkueet"] = toteuta("""
            SELECT j.id, j.joukkuenimi AS nimi
            FROM joukkueet j, sarjat s
            WHERE j.sarja = s.id
            AND s.id = %s
        """, parametrit=(sarja_id,))
    except KeyError:
        # Sessiomuuttujan avainvirheiden tapahtuessa palataan aina takaisin sarjalistaussivulle.
        return redirect(url_for("admin_sarjat"))
    # Luodaan instanssi joukkueluontilomakkeesta ja avataan joukkuelistaussivu.
    lomake = Admin_JoukkueLuonti(sarja_id=session["sarja"]["id"])
    return render_template('admin_joukkueet.html', joukkueet=session["joukkueet"], lomake=lomake)


@app.route('/admin_tallenna_joukkue_uusi', methods=['POST'])
@admin_auth
def admin_tallenna_joukkue_uusi():
    """ Hoitaa joukkueen lisäyslomkkeen validoinnin ja sen läpäistessään myös uuden joukkueen lisäämisen.
    Käsittelee uusien jäsenkenttien lisäämisen, jos on painettu "Alusta tyhjä" painiketta.
    """
    lomake = Admin_JoukkueLuonti(request.form, sarja_id=session["sarja"]["id"])
    joukkueet = []
    for joukkue in session["joukkueet"]:
        joukkueet.append({"id": joukkue["id"], "nimi": joukkue["nimi"]})
    # Tarkistetaan painettiinko "Alusta tyhjä" -painiketta.
    if request.form.get("lisays", ""):
        # Jos painettiin, avataan sama adminin joukkuelistaussivu alustetulla jäsenkentällä uudelleen.
        return render_template('admin_joukkueet.html', lomake=lomake, joukkueet=joukkueet)
    # Muussa tapauksessa jatketaan joukkueen lisäämiseen.
    id = generoiId() # Generoidaan joukkueelle uusi ainutlaatuinen id.
    nimi = lomake.nimi.data # Haetaan syötetty nimi lomakkeesta.
    salasana = generoiSalasana(id, lomake.salasana.data) # Generoidaan uusi salasana lomakkeeseen syötetyn merkkijonon perusteella.
    jasenet = []
    # Haetaan syötetyt jäsenet lomakkeesta.
    for jasen in lomake.jasenet.data:
        if jasen.strip():
            jasenet.append(jasen)
    # Validoidaan lomake.
    if not lomake.validate():
        # Jos validointia ei läpäistä, palataan takaisin joukkuelistaussivulle lisäämättä joukkuetta.
        return render_template('admin_joukkueet.html', lomake=lomake, joukkueet=joukkueet)
    try:
        # Jos validointi läpäistään, lisätään luotu joukkue tietokantaan valittuun sarjaan.
        toteuta("""
            INSERT INTO joukkueet (id, joukkuenimi, salasana, sarja, jasenet)
            VALUES (%s, %s, %s, %s, %s)
        """, parametrit=(id, nimi, salasana, session["sarja"]["id"], json.dumps(jasenet)), hae=False)
    except Exception:
        # Jos tallentamisessa tapahtui ongelmia, ilmoitetaan virheestä ja palataan joukkuelistaussivulle.
        flash("Joukkueen tallennus eponnistui.", "error")
        return redirect(url_for("admin_joukkueet"), lomake=lomake)
    # Valitaan luotu joukkue ja tallennetaan myös muuttuneet tiedot sessiomuuttujiin.
    session["joukkue"] = {"id": id, "nimi": nimi, "salasana": salasana, "sarja": session["sarja"]["id"]}
    session["jasenet"] = jasenet
    # Avataan lopuksi joukkuelistaussivu uudelleen.
    return redirect(url_for("admin_joukkueet"))


class Admin_JoukkueMuokkaus(PolyglotForm):
    """ Luokka generoimaan admin käyttäjän joukkueen muokkaamislomakkeen.
    """
    def __init__(self, formdata=None, sarjat=[], sarja_id=-1, **kwargs):
        super().__init__(formdata, **kwargs)
        self.sarja_id = sarja_id # Lisätään valitun sarjan id attribuutiksi.
        self.sarja.choices = sarjat # Asetetaan sarjat parametri vaihtotehdoiksi RadioFieldille.
        # Otetaan jo olemassa olevien jäsenkenttien sisältö tilapäiseen temp-muuttujaan.
        temp = self.jasenet.data
        # Poistetaan FieldListin kaikki jäsenkentät (StringField).
        while self.jasenet.data:
            self.jasenet.pop_entry()
        # Täytetään FieldList uudestaan niillä jäsenkentillä, joissa oli jotakin sisältöä temp-muuttujan arvoja hyödyntäen.
        i = 1
        for jasen in temp:
            if jasen.strip():
                self.jasenet.append_entry(jasen)
                self.jasenet[-1].label = f"Jäsen {i}"
                i += 1
        # Lisätään täytettyjen kenttien perään vielä yksi tyhjä jäsenkenttä mahdollista uutta jäsentä varten.
        self.jasenet.append_entry("")
        self.jasenet[-1].label = f"Jäsen {i}"
        i += 1
        # Tarkistetaan, että vähintään kaksi jäsenkenttää löytyy ja lisätään vielä toinen tarvittaessa.
        if len(self.jasenet) < 2:
            self.jasenet.append_entry("")
            self.jasenet[-1].label = f"Jäsen {i}"
    
    def joukkueenNimi():
        """ Validaattori joukkueen nimisyötteelle.
        """
        def _joukkueenNimi(self, field):
            # Tarkistetaan onko joukkuekentässä sisältöä.
            onkoTaytetty = field.data and len(field.data.strip()) or 0
            if not onkoTaytetty:
                # Jos ei, asetetaan validointivirhe.
                raise ValidationError(f"Joukkue tarvitsee nimen.")
            # Tarkistetaan onko syötetty nimi jo jonkin muun kuin muokattavan joukkueen käytössä.
            syotettyNimi = field.data.lower().strip()
            aiempiNimi = session["joukkue"]["nimi"].lower().strip()
            if syotettyNimi == aiempiNimi:
                return
            joukkueet = toteuta("""
                SELECT joukkuenimi AS nimi
                FROM joukkueet
                WHERE sarja = %s
            """, parametrit=(self.sarja_id,))
            for joukkue in joukkueet:
                verrattavaNimi = joukkue["nimi"].lower().strip()
                if syotettyNimi == verrattavaNimi:
                    # Jos on, asetetaan validointivirhe.
                    raise ValidationError(f'Joukkueen nimi "{field.data}" on jo käytössä.')
        return _joukkueenNimi

    def jasenkenttienNimet():
        """ Validaattori joukkueen jäsensyötteille.
        """
        def _jasenkenttienNimet(self, field):
            # Haetaan ne jäsenkentät, joissa on jotakin sisältöä.
            oikeat_jasenet = [jasen.lower().strip() for jasen in self.jasenet.data if jasen.strip()]
            if len(oikeat_jasenet) < 2:
                # Jos sisällöllisiä kenttiä on vähemmän kuin kaksi, asetetaan validointivirhe.
                raise ValidationError(f"Joukkueella on oltava vähintään kaksi jäsentä.")
            # Tarkistetaan onko jokaisen jäsenkentän sisältö aintulaatuinen.
            ovatko_nimet_ainutlaatuisia = len(oikeat_jasenet) == len(set(oikeat_jasenet))
            if not ovatko_nimet_ainutlaatuisia:
                # Jos ei ole, asetetaan validointivirhe.
                raise ValidationError(f"Joukkueen jäsenillä ei saa olla samoja nimiä.")
        return _jasenkenttienNimet

    # Luodaan lomakkeen sisältö.
    nimi = StringField("Joukkueen nimi", validators=[joukkueenNimi()])
    salasana = PasswordField("Salasana", default="")
    sarja = RadioField("Sarja", validators=[validators.InputRequired()])
    jasenet = FieldList(StringField(validators=[jasenkenttienNimet()]))
    lisays = SubmitField("Alusta tyhjä", default="uusi")
    poisto = BooleanField("Poista joukkue", default=False)
    tallennus = SubmitField("Tallenna", default="tallenna")


@app.route('/admin_joukkue_muokkaus', methods=['GET', 'POST'])
@admin_auth
def admin_joukkue_muokkaus():
    """ Hakee tiedot joukkueesta, joka on valittu tai luotu ja esitäyttää joukkueen muokkauslomakkeen kyseisen joukkueen datalla.
    Avaa näkymän, jossa käyttäjä voi muokata joukkueensa tietoja.
    """
    # Haetaan polun parametreistä "joukkue":en arvo.
    joukkue_id = request.args.get("joukkue", "")
    if joukkue_id:
        try:
            # Jos löytyy, haetaan parametriä vastaavan joukkueen tiedot ja asetetaan session sarjaksi.
            queryData_joukkue = toteuta("""
                SELECT j.joukkuenimi, j.id, j.salasana, j.jasenet, j.sarja
                FROM joukkueet j, sarjat s, kilpailut k
                WHERE j.id = %s
                AND s.id = j.sarja
                AND k.id = s.kilpailu
                AND k.id = %s
            """, parametrit=(joukkue_id, session["kilpailu"]["id"]), yksi=True)
            session["joukkue"] = {"id": joukkue_id, "nimi": queryData_joukkue["joukkuenimi"], "sarja": queryData_joukkue["sarja"]}
            session["jasenet"] = json.loads(queryData_joukkue["jasenet"])
        except TypeError:
            # Jos annettu parametri oli huono, palataan takaisin joukkuelistaussivulle ja ilmoitetaan virheestä.
            flash("Haettua joukkuetta ei löytynyt!", "search")
            return redirect(url_for("admin_joukkueet"))
    else:
        try:
            # Jos sarja parametriä ei löydy, käytetään session nykyistä joukkuetta.
            joukkue_id = session["joukkue"]["id"]
        except KeyError:
            # Jos sitäkään ei ole, palataan takaisin joukkuelistaussivulle.
            return redirect(url_for("admin_joukkueet"))
    queryData_joukkueenSarjat = toteuta("""
        SELECT s.id, s.sarjanimi
        FROM sarjat s, kilpailut k
        WHERE s.kilpailu = %s
        GROUP BY s.id, s.sarjanimi
        ORDER BY s.sarjanimi ASC
    """, parametrit=(session["kilpailu"]["id"],))
    sarjat = []
    for sarja in queryData_joukkueenSarjat:
        sarjat.append((sarja["id"], sarja["sarjanimi"]))
    session["kilpailu"]["sarjat"] = sarjat
    # Luodaan instanssi adminin joukkueen muokkauslomakkeesta ja avataan adminin joukkueen muokkaussivu.
    lomake = Admin_JoukkueMuokkaus(sarjat=session["kilpailu"]["sarjat"], sarja=session['joukkue']["sarja"], nimi=session['joukkue']["nimi"], jasenet=session["jasenet"], sarja_id=session["sarja"]["id"])
    return render_template('admin_joukkue_muokkaus.html', lomake=lomake)


@app.route('/admin_tallenna_joukkue', methods=['POST'])
@admin_auth
def admin_tallenna_joukkue():
    """ Hoitaa joukkueen muokkauslomkkeen validoinnin ja sen läpäistessään myös joukkueeseen tehtyjen muutosten tallentamisen.
    Käsittelee uusien jäsenkenttien lisäämisen, jos on painettu "Alusta tyhjä" painiketta.
    """
    lomake = Admin_JoukkueMuokkaus(request.form, sarjat=session["kilpailu"]["sarjat"], sarja_id=session["sarja"]["id"])
    # Tarkistetaan oliko joukkueen poistocheckbox valittuna, kun tallennuspainiketta painettiin.
    if request.form.get("tallennus", "") and request.form.get("poisto", ""):
        # Jos oli, tarkistetaan vielä oliko joukkueella olemassa olevia leimauksia.
        leimaukset = toteuta("""
            SELECT j.joukkuenimi, COUNT(t.joukkue) AS leimauksia
            FROM joukkueet j
            LEFT OUTER JOIN tupa t
            ON j.id = t.joukkue
            WHERE j.sarja = %s
            AND j.joukkuenimi = %s
            GROUP BY j.joukkuenimi
        """, parametrit=(session["joukkue"]["sarja"], session["joukkue"]["nimi"]), yksi=True)
        if 0 < leimaukset["leimauksia"]:
            # Jos leimauksia oli, lisätään virheviesti ja palataan takaisin adminin joukkueen muokkausnäkymään poistamatta joukkuetta.
            flash(f'Ei voi poistaa: joukkueella "{session["joukkue"]["nimi"]}" on leimauksia!', "error")
            return redirect(url_for("admin_joukkue_muokkaus"))
        # Poistetaan joukkue tietokannasta.
        toteuta("""
            DELETE FROM joukkueet WHERE id = %s
        """, parametrit=(session["joukkue"]["id"],), hae=False, yksi=True)
        # Nollataan session joukkue.
        nollaa_joukkue()
        # Palataan takaisin joukkuelistaussivulle.
        return redirect(url_for("admin_joukkueet"))
    # Tarkistetaan painettiinko "Alusta tyhjä" -painiketta.
    elif request.form.get("lisays", ""):
        # Jos painettiin, avataan sama adminin joukkueen muokkausnäkymä alustetulla jäsenkentällä uudelleen.
        return render_template('admin_joukkue_muokkaus.html', lomake=lomake)
    # Muussa tapauksessa jatketaan joukkueen tallentamiseen.
    id = session["joukkue"]["id"] # Käytetään joukkueen jo olemassa olevaa id:tä.
    nimi = lomake.nimi.data # Haetaan syötetty nimi lomakkeesta.
    salasana = generoiSalasana(id, lomake.salasana.data) # Generoidaan uusi salasana lomakkeeseen syötyetyn merkkijonon perusteella.
    sarja = lomake.sarja.data # Haetaan valittu sarja lomakkeesta.
    jasenet = []
    # Haetaan syötetyt jäsenet lomakkeesta.
    for jasen in lomake.jasenet.data:
        if jasen.strip():
            jasenet.append(jasen)
    # Validoidaan lomake.
    if not lomake.validate():
        # Jos validointia ei läpäistä, palataan takaisin joukkueen muokkausnäkymään tallentamatta muutoksia.
        return render_template('admin_joukkue_muokkaus.html', lomake=lomake)
    # Jos validointi läpäistään, päivitetään joukkueen tiedot tietokantaan.
    toteuta("""
        UPDATE joukkueet
        SET joukkuenimi = %s, salasana = %s, sarja = %s, jasenet = %s
        WHERE id = %s
    """, parametrit=(nimi, salasana, sarja, json.dumps(jasenet), id), hae=False)
    # Tallennetaan myös muuttuneet tiedot sessiomuuttujiin.
    session["joukkue"]["nimi"] = nimi
    session["joukkue"]["salasana"] = salasana
    session["joukkue"]["sarja"] = sarja
    session["jasenet"] = jasenet
    # Avataan lopuksi adminin joukkueen muokkausnäkymä uudelleen.
    return redirect(url_for("admin_joukkue_muokkaus"))


@app.route('/admin_listaus', methods=(['GET', 'POST']))
@admin_auth
def admin_listaus():
    """ Hakee kaikki valitun kilpailun rastit tietoineen sekä leimauskertymineen ja avaa sivun, jolla kyseiset tiedot listataan.
    """
    # Jos sessiolla ei ole valittua kilpailua, palataan takaisin kilpailulistaussivulle.
    try:
        if not session["kilpailu"]:
            return redirect(url_for("admin_kilpailut"))
    except:
        return redirect(url_for("admin_kilpailut"))
    # Haetaan rastien tiedot ja leimauskerrat tietokannasta hyödyntäen ulkoista liitosta.
    rastit = toteuta("""
        SELECT r.koodi, r.lat, r.lon, COUNT(t.rasti) AS leimauksia
        FROM rastit r
        LEFT OUTER JOIN tupa t
        ON r.id = t.rasti
        WHERE r.kilpailu = %s
        GROUP BY r.koodi, r.lat, r.lon
        ORDER BY leimauksia DESC
        """, parametrit=(session["kilpailu"]["id"],))
    # Avataan valitun kilpailun rastilistaussivu.
    return render_template('admin_listaus.html', rastit=rastit)


@app.route('/admin_logout')
def admin_logout():
    """ Hoitaa admin käyttäjän uloskirjaamisen tyhjentämällä sessiomuuttujat ja ohjaamalla takaisin kirjautumissivulle.
    """
    # Vaihtoehtoinen tapa tyhjentää: [session.pop(key) for key in list(session.keys())]
    session.clear()
    return redirect(url_for('admin_kirjaudu'))




# ========== APUOHJELMAT ==========


def generoiId():
    """ Hakee suurimman id:n tietokannan kaikista joukkueista ja palauttaa sitä yhtä suuremman kokonaisluvun.
    """
    id = None
    joukkueet = toteuta("SELECT id FROM joukkueet")
    for joukkue in joukkueet:
        try:
            joukkueenId = int(joukkue["id"])
            if not id or id <= joukkueenId:
                id = joukkueenId + 1
        except ValueError: # Jos joukkueella epäkelpo id, skipataan.
            continue
    if not id: # Jos id:n arvo edelleen None, palautetaan 1.
        return 1
    return id


def generoiSalasana(osa1, osa2):
    """ Generoi ja palauttaa heksadesimaalisalasanan parametriarvojen pohjalta.

    :param osa1: Salasanan etuliite, jolla turvataan varsinainen salasana.
    :param osa2: Varsinainen salasana.
    """
    salasana = str(osa2).strip()
    if not salasana: # Jos salasanaa ei ole annettu, asetetaan oletussalasanaksi "ties4080".
        salasana = "ties4080"
    m = hashlib.sha512()
    m.update(str(osa1).encode("UTF-8"))
    m.update(salasana.encode("UTF-8"))
    return m.hexdigest()


def nollaa_sarja():
    """ Alustetaan manuaalisesti session sarjamuuttuja.
    """
    try:
        session.pop('sarja', None)
    except:
        pass


def nollaa_joukkue():
    """ Alustetaan manuaalisesti session joukkuemuuttuja.
    """
    try:
        session.pop('joukkue', None)
    except:
        pass
