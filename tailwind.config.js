// Farben, Abstaende und Schriftgroessen der Website.
// Nach Aenderungen an den HTML-Klassen neu erzeugen: bash scripts/build-css.sh
const forms = require('@tailwindcss/forms');
const containerQueries = require('@tailwindcss/container-queries');

module.exports = {
  plugins: [forms, containerQueries],
  "darkMode": "class",
  "theme": {
    "extend": {
      "colors": {
        "on-tertiary-fixed-variant": "#434844",
        "surface-container-low": "#f4f4ee",
        "on-background": "#1a1c19",
        "background": "#fafaf4",
        "on-primary-container": "#92ce9a",
        "on-error": "#ffffff",
        "tertiary": "#343835",
        "error": "#ba1a1a",
        "on-primary-fixed": "#00210a",
        "on-secondary-fixed-variant": "#3c4b35",
        "surface-dim": "#dadad5",
        "surface": "#fafaf4",
        "secondary": "#54634b",
        "surface-container-highest": "#e3e3de",
        "error-container": "#ffdad6",
        "surface-container": "#eeeee9",
        "tertiary-fixed": "#dfe4df",
        "on-surface": "#1a1c19",
        "on-secondary": "#ffffff",
        "secondary-fixed-dim": "#bbccaf",
        "surface-bright": "#fafaf4",
        "on-primary": "#ffffff",
        "outline": "#717970",
        "on-tertiary-fixed": "#181d1a",
        "primary": "#01411b",
        "on-error-container": "#93000a",
        "secondary-container": "#d4e5c7",
        "surface-container-lowest": "#ffffff",
        "inverse-on-surface": "#f1f1ec",
        "on-primary-fixed-variant": "#175129",
        "outline-variant": "#c0c9be",
        "surface-variant": "#e3e3de",
        "on-tertiary-container": "#bcc1bc",
        "tertiary-container": "#4a4f4c",
        "surface-container-high": "#e8e8e3",
        "inverse-primary": "#98d5a0",
        "on-tertiary": "#ffffff",
        "primary-fixed-dim": "#98d5a0",
        "primary-fixed": "#b4f1bb",
        "primary-container": "#205930",
        "on-secondary-fixed": "#121f0c",
        "tertiary-fixed-dim": "#c3c8c3",
        "secondary-fixed": "#d7e8ca",
        "on-surface-variant": "#414940",
        "inverse-surface": "#2f312e",
        "surface-tint": "#316a3f",
        "on-secondary-container": "#58674f"
      },
      "borderRadius": {
        "DEFAULT": "0.25rem",
        "lg": "0.5rem",
        "xl": "0.75rem",
        "full": "9999px"
      },
      "spacing": {
        "section-gap": "120px",
        "stack-lg": "32px",
        "stack-sm": "8px",
        "stack-md": "16px",
        "container-max": "1140px",
        "gutter": "24px"
      },
      "fontFamily": {
        "display-lg": [
          "Montserrat"
        ],
        "label-sm": [
          "Inter"
        ],
        "body-lg": [
          "Inter"
        ],
        "headline-md": [
          "Montserrat"
        ],
        "body-md": [
          "Inter"
        ],
        "display-lg-mobile": [
          "Montserrat"
        ]
      },
      "fontSize": {
        "display-lg": [
          "48px",
          {
            "lineHeight": "1.1",
            "letterSpacing": "0.05em",
            "fontWeight": "600"
          }
        ],
        "label-sm": [
          "12px",
          {
            "lineHeight": "1",
            "letterSpacing": "0.1em",
            "fontWeight": "600"
          }
        ],
        "body-lg": [
          "18px",
          {
            "lineHeight": "1.6",
            "letterSpacing": "0",
            "fontWeight": "400"
          }
        ],
        "headline-md": [
          "24px",
          {
            "lineHeight": "1.3",
            "letterSpacing": "0.03em",
            "fontWeight": "500"
          }
        ],
        "body-md": [
          "16px",
          {
            "lineHeight": "1.6",
            "letterSpacing": "0",
            "fontWeight": "400"
          }
        ],
        "display-lg-mobile": [
          "32px",
          {
            "lineHeight": "1.2",
            "letterSpacing": "0.04em",
            "fontWeight": "600"
          }
        ]
      }
    }
  },
  "content": [
    "*.html"
  ]
};
