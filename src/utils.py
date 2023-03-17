from ochanticipy import CodAB, create_country_config

country_config = create_country_config(iso3="bgd")

codab = CodAB(country_config=country_config)
admin0 = codab.load(admin_level=0)
