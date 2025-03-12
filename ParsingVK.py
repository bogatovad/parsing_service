import vk_api
import os
from dotenv import load_dotenv
from exeptions import ExeptionCheckAnswerKeys
from logger_config import logger




class ParsingVK():
    def __init__(self):
        load_dotenv()
        self.ACCESS_TOKEN = os.getenv("SERVICE_KEY")
        self.check_tokens(self.ACCESS_TOKEN)
        self.VERSION_VK_API = 5.199


    def create_vk_session(self):
        vk_session = vk_api.VkApi(token=self.ACCESS_TOKEN)
        vk = vk_session.get_api()
        return vk

    def loading_group_ids(self):
        '''Приводим из формата https://vk.com/torpedonn -> torpedonn'''
        with open("groupsID_for_parsing.txt", "r", encoding="utf-8") as file:
            lines = [line.strip().rsplit("/", 1)[-1] for line in file]
        return lines
    

    def check_tokens(self, ACCESS_TOKEN):
        if not ACCESS_TOKEN:
            message = "Отсутствует обязательная переменная окружения {ACCESS_TOKEN}"
            logger.critical(message)
            raise ValueError("Нет переменной окружения SERVICE_KEY")
        

    def check_api_response_fields(self):
        '''Проверка полей response на соответствие типу'''
        for i in range(self.count_posts):
            if not isinstance(self.response["items"][i]["text"], str):
                message = 'Поле text, пришло не ввиде строки.'
                logger.error(message)
                raise ValueError(message)  
            

    def check_api_response(self):
        '''Проверяется валидность ответа API'''
        if not isinstance(self.response, dict):
            message = "Response пришёл не ввиде словаря"
            logger.error(message) 
            raise TypeError("Response пришёл не ввиде словаря")
        
        if "items" not in self.response:
            message = 'Ключа items нет в response'
            logger.error(message) 
            raise ExeptionCheckAnswerKeys(message)
        
        for i in range(self.count_posts):
            if "text" not in self.response["items"][i]:
                message = "В ответе нет ключа text"
                logger.error(message)
                raise ExeptionCheckAnswerKeys(message)
        self.check_api_response_fields()

    
    def parsing(self, count=None):
        '''Парсинг'''
        vk = self.create_vk_session()
        self.count_posts = count if count is not None else 3
        GROUPS_ID = self.loading_group_ids()
        self.response = vk.wall.get(domain=GROUPS_ID[27], v=self.VERSION_VK_API, count=self.count_posts)
        self.check_api_response()
        self.post_list = []


    def filter_content(self) -> list[dict]:
        '''
        Приводим спаршенный контент в нужную форму.
        Пока что форма [{'id': 0, 'text': ''}]
        id - кастомный, просто нумерация
        '''
        for i in range(self.count_posts):
            post = {}
            post_text = self.response["items"][i]["text"]
            post["id"] = i
            post["text"] = post_text
            self.post_list.append(post)
    

    def get_filter_data(self):
        return self.post_list
    

    def preaty_print(self):
        '''Печать постов через чёрточку(для консоли)'''
        for i in range(len(self.post_list)):
            print("-------------------------------------------------------------")
            print(self.post_list[i])







if __name__ == "__main__":
    parser_vk = ParsingVK()
    parser_vk.parsing(count=5)
    parser_vk.filter_content()
    parser_vk.preaty_print()
    logger.info("Выполнилось")
