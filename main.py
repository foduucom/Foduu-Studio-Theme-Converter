from src.main import main,give_full_theme_data

if __name__ == "__main__":
    theme_data = {
    "THEME_NAME": "Gearo Furniture Store Ecommerce",
    "VERSION": "1.0.1",
    "CATEGORY": "business",
    "SUBCATEGORY": "corporate",
    "WEBSITE_TYPE": "both",
    "AUTHOR": "Kirti Pogra",
    "AUTHOR_EMAIL": "john.doe@example.com",
    "DEMO_URL": "https://demo.example.com/modern-business-pro"
    }

    # theme_path = "THEMES/extech-it-solutions-services.zip"
    # theme_path = "THEMES/business-corporate-finance.zip"
    # theme_path = "THEMES/fllopi-flooring-tiling.zip"
    theme_path = "THEMES/gearo_furniture_store_ecommerce.zip"
    # theme_path = "THEMES/Logtra_v1.zip"
    # theme_path = "THEMES/rasm-beauty-spa-care-nail-salon.zip"
    main(theme_path,
         theme_data)

    # print(give_full_theme_data(theme_data))