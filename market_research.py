import repaon as repa
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

chrome_options = Options()
chrome_options.add_argument('--disable-extensions')
chrome_options.add_argument('--start-maximized')
chrome_options.add_argument('--start-fullscreen')
chrome_driver = webdriver.Chrome(
    executable_path=repa.DRIVER_CHROME_PATH,
    options=chrome_options)

# for region in repa.REGIONS:
#     flat_ids = repa.get_offer_ids_w_prices(
#         chrome_driver,
#         repa.REGIONS[3],
#         repa.REALTY_RESIDENTAL,
#         repa.OFFER_SALE)
#     break
# print(flat_ids)
# if len(flat_ids) > 0:
#     flat_ids = repa.remove_saved(flat_ids)
# print(flat_ids)
# for id in flat_ids:
repa.get_offer_info(chrome_driver, '489010836')
chrome_driver.close
