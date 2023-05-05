import repaon
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

chrome_options = Options()
chrome_options.add_argument('--disable-extensions')
chrome_options.add_argument('--start-maximized')
chrome_options.add_argument('--start-fullscreen')
chrome_driver = webdriver.Chrome(
    executable_path=repaon.DRIVER_CHROME_PATH,
    options=chrome_options)

for region in repaon.REGIONS:
    flat_ids = repaon.get_offer_ids_w_prices(
        chrome_driver,
        repaon.REGIONS[3],
        repaon.REALTY_RESIDENTAL,
        repaon.OFFER_SALE)
    break
flat_ids = repaon.remove_saved(flat_ids)
print(flat_ids)
chrome_driver.close
