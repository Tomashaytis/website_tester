from website_tester import WebsiteTester

if __name__ == '__main__':
    tester = WebsiteTester("https://www.bitrix24.ru/prices/", 100, 5, 5)
    tester.start_testing()
