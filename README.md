# Product Trustworthiness Score: frontend prototype

SC4025 Team 2 · Amazon India. A working prototype of the seller-offer authenticity check, matching the Figma hi-fi frames.

Concept prototype for coursework, not an actual Amazon.in page. Sellers, ratings, reviews and scores are fictional.

## How it fits together

There is one frontend. It reads everything it shows from `data.json`:

```
Backend scoring (rule-based)  ──writes──▶  data.json  ──read by──▶  index.html + app.js
```

The four seller states (High, Medium, Low, Not enough data) are not four pages. They are four entries in `data.json`, and the same page draws whichever one is selected. To change what the page shows, change `data.json`. No frontend code changes are needed.

## Run it

Browsers block reading a JSON file when `index.html` is opened by double-clicking, so use a local server:

- **VS Code:** install the Live Server extension, right-click `index.html`, choose **Open with Live Server**.
- **Terminal:** in this folder run `python -m http.server 8000`, then open <http://localhost:8000>.
- **GitHub Pages:** works with no extra steps once Pages is turned on for this repo.

If the page shows a red box instead of the product, it explains what went wrong (usually opened by double-click, or `data.json` has a problem).

Useful URL options:

| Option | Example | Effect |
| --- | --- | --- |
| `seller` | `?seller=C` | Starts on that seller's offer |
| `data` | `?data=backend-output.json` | Loads a different JSON file, handy for testing backend output without overwriting `data.json` |

## Files

| File | Purpose |
| --- | --- |
| `index.html` | Page structure: header, product details, buy box, side panels, cart |
| `styles.css` | Styling, including tablet and phone layouts |
| `app.js` | Loads and checks `data.json`, then handles switching seller, "Why this score", compare offers, how it works, cart |
| `data.json` | The product and its seller offers. **Produced by the backend.** The current file is demo data. |
| `assets/product.jpg` | Product photo referenced by `product.image` |

## For the backend team: what to output

Your scoring code should write one file, `data.json`, in the shape below. The current `data.json` is a complete working example; matching its structure is the easiest way to get it right.

### Top level

| Field | Type | Notes |
| --- | --- | --- |
| `updated` | string `YYYY-MM-DD` | Date the scores were calculated. Shown as "Updated …" on each factor. |
| `product` | object | The product being sold (see below) |
| `sellers` | list | One entry per seller offering this product |

`_note` is a comment for humans and is ignored.

### `product`

| Field | Type | Notes |
| --- | --- | --- |
| `title` | string | Full listing title |
| `shortTitle` | string | Short name used in the panels and cart |
| `store` | string | Brand store link text |
| `rating` | number | Average star rating for the product, 0 to 5 |
| `ratingCount` | number | Number of ratings |
| `image` | string | Path to the product photo |
| `breadcrumb` | list of strings | Category path |
| `bullets` | list of strings | "About this item" points |

### Each entry in `sellers`

| Field | Type | Notes |
| --- | --- | --- |
| `id` | string | Short unique id, for example `"A"` |
| `name` | string | Seller name |
| `price` | number | Price in rupees, a plain number such as `254900` (the page adds ₹ and commas) |
| `delivery` | string | Delivery line |
| `band` | string | Exactly one of `High`, `Medium`, `Low`, `Not enough data` |
| `score` | number or `null` | 0 to 100. Must be `null` when `band` is `Not enough data`. Not shown to shoppers (the page shows the band only); kept so the team can check the band cut-offs |
| `reason` | string or `null` | One line explaining why there is not enough data. Required for `Not enough data`, otherwise `null` |
| `inline` | list of 3 factor keys | Which three factors appear in the buy box, for example `["price", "history", "brand"]` |
| `factors` | object | All five factors, keyed as below |

### `factors`

Always include all five keys: `history`, `brand`, `price`, `reviews`, `complaints`. Each one has:

| Field | Type | Notes |
| --- | --- | --- |
| `status` | string | `pass`, `warn` or `na` (not available) |
| `short` | string | Short line for the buy box |
| `text` | string | Full sentence for the "Why this score" panel |
| `source` | string | Where the data came from, for example `"Brand Registry"` |

`factors.reviews` also has:

| Field | Type | Notes |
| --- | --- | --- |
| `flagged` | list | Up to 5 reviews behind the warning, each `{ "tag", "stars", "text" }`. `tag` is `Authenticity`, `Wrong item` or `Description mismatch`. Use `[]` when there are none. |
| `excludedDuplicates` | number | How many near-duplicate reviews were removed before scoring |

### What the backend decides and what the frontend works out

| Backend decides | Frontend works out from that |
| --- | --- |
| The band and score for each offer | Which offers count as "higher-scoring" (by band) |
| Each factor's status and wording | The compare link wording ("2 offers with a higher score") |
| Whether the price is far below other sellers (set `factors.price.status` to `warn`) | Showing the red price warning, which appears only when `factors.price.status` is `warn` |
| Which three factors to show inline | Price differences, sort order (band, then price), ₹ formatting |

### Rules the scoring should follow

These are the agreed thresholds from the user stories. Confirm or change them as a team, then keep the frontend wording in line.

- Not enough data: fewer than 20 reviews or under 90 days of seller history.
- Price warning: offer more than 30% below the other sellers' prices for the same product.
- Band cut-offs for High, Medium and Low: to be agreed.

### Checking your output

Load your file with `?data=your-file.json`. If anything is missing or the wrong type, the page lists each problem (for example `sellers[2].score must be a number, or null when band is Not enough data`) instead of showing a broken page. When it shows the product, your file is valid.

## What the frontend covers

| Story | Feature |
| --- | --- |
| US1 | Score band beside Add to Cart, with three key factors; tapping the band opens the explanation |
| US2 | Band labelled "Authenticity check" with a shield, kept apart from the star rating; no number out of 100 is shown anywhere |
| US3 | "Why this score" panel: five factors in a fixed order, each with status, source and date |
| US4 | Price warning when an offer is far below other sellers, with their usual price range |
| US5 | Compare the same product from higher-scoring sellers; one tap to switch |
| US6 | "Not enough data" state with a reason and no warning wording |
| US7 | Flagged reviews behind the review-pattern factor (expand to view) |
| US8 | "How the authenticity check works" panel |

The yellow demo bar at the top lets testers start from any seller. Each one is a persona flow: A High (Rohan), C Low (Aditi), B Medium (Neha), D Not enough data (edge case).

## Notes on quality

- All data is written with `textContent`, never `innerHTML`, so backend output cannot inject markup.
- `data.json` is checked on load, and problems are listed on the page.
- Bands and statuses use distinct icon shapes as well as colour (WCAG 2.1).
- Panels close with Escape, the Close button or a click outside, and focus returns to where it was.
- Layout adapts to desktop, tablet and phone widths.
