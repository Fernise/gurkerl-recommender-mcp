# Scoring

Scores are open-ended, not a 0-100 percentage.

Current rough interpretation:

- `110+`: excellent match
- `90-109`: strong match
- `70-89`: good match
- `60-69`: maybe worth checking
- `<60`: usually not worth notifying

The default Telegram config uses a threshold of `85`.

## What Adds Points

- high-priority category such as meat, fish, dairy, eggs, legumes
- meaningful protein per 100g
- low sugar
- calories in a gym-friendly range
- promotion discount
- Save Food / close-to-expiry discount
- strong price per protein
- liked brand, once configured

## What Removes Points Or Adds Cautions

- high sugar
- expensive for the protein it gives
- calorie dense items
- disliked brand, once configured
- expiring meat/fish gets a warning even when it is a good buy

The public Gurkerl source does not provide full nutrition labels for every item,
so some nutrition values are estimates by category/name. This is enough for
alerts, but not a replacement for checking the final product page.

Telegram messages include the nutrition source:

- `exact`: parsed from product details or a trusted structured source
- `estimated`: inferred from category/product name
- `unavailable`: no usable nutrition data found; current public monitor normally
  falls back to `estimated` instead
