document.addEventListener("DOMContentLoaded", function () {
	// Function to update the price label based on the selected order type.
	function updatePriceLabel() {
		let selectedType = document.querySelector(
			'input[name="type"]:checked'
		).value;
		let priceLabel = document.getElementById("price-label");

		if (selectedType === "Bid") {
			priceLabel.textContent = "Max Price ($):";
		} else {
			priceLabel.textContent = "Min Price ($):";
		}
	}

	// Attach the event listener to the radio buttons.
	document.querySelectorAll('input[name="type"]').forEach(function (radio) {
		radio.addEventListener("change", updatePriceLabel);
	});

	// Perform an initial update in case a value is pre-selected.
	updatePriceLabel();
});
