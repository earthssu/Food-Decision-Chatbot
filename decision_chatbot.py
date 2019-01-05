from flask import Flask
from flask import request
from flask import jsonify
from flask import json
import re
from math import ceil
import random

import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

count_num = -1 #질문 개수 설정
tag_set = set() #태그 모음
tag_list = []
point_dict = dict() #점수 부여
ABCDE_dict = {'A':2, 'B':1, 'C':0, 'D':-1, 'E':-2} #점수 딕셔너리
lines = [] #음식점 저장 딕셔너리
a_tag = str()

@app.route("/keyboard", methods=["GET"])
def keyboard():
    response = {
        "type": "buttons",
        "buttons": ["대화 시작하기"]
    }
    response = json.dumps(response, ensure_ascii=False)
    return response


@app.route("/message", methods=["POST"])
def message():
    data = json.loads(request.data)
    content = data["content"]
    global count_num
    global a_tag
    global tag_list
    global point_dict
    global ABCDE_dict
    global lines
    global tag_set

    if content == "대화 시작하기":  # 지역 입력
        text = "원하는 키워드를 입력해주세요\n" + "ex) 영통, 안양 고기, 경주 한식\n" + "지역명은 입력 필수입니다"
        response = {
            "message": {
                "text": text
            }
        }

    elif str(content).isdigit(): # 최초 태그 평가 #태그 개수 설정

        count_num = int(content)
        print(count_num)

        tag_list = list(tag_set)
        rand_num = int(random.random() * 100)
        a_tag = tag_list[rand_num % len(tag_list)]
        count_num = count_num - 1
        if a_tag == '': tag_list.remove(a_tag)
        text = "'{}'(이)라는 tag 가 붙은 곳은 어떠신가요?\n".format(a_tag)
        text += "A : 매우 좋음\n"
        text += "B : 좋음\n"
        text += "C : 모르겠음\n"
        text += "D : 별로\n"
        text += "E : 매우 별로\n"
        response = {
            "message": {
                "text": text
            },
            "keyboard": {
                "type": "buttons",
                "buttons": [
                    "A",
                    "B",
                    "C",
                    "D",
                    "E"
                ]
            }
        }

    elif count_num > 0 and (content=="A" or content =="B" or content=="C" or content=="D" or content=="E"): #평가하기

        count_num = count_num - 1

        content = ABCDE_dict[content]
        point_dict[a_tag] = content

        for line in lines:
            for a_tag in list(point_dict.keys()):
                if a_tag in line['특징']:
                    line['점수'] += point_dict[a_tag]

        tag_list.remove(a_tag)
        rand_num = int(random.random() * 100)
        a_tag = tag_list[rand_num % len(tag_list)]

        text = "'{}'(이)라는 tag 가 붙은 곳은 어떠신가요?\n".format(a_tag)
        text += "A : 매우 좋음\n"
        text += "B : 좋음\n"
        text += "C : 모르겠음\n"
        text += "D : 별로\n"
        text += "E : 매우 별로\n"
        response = {
            "message": {
                "text": text
            },
            "keyboard": {
                "type": "buttons",
                "buttons": [
                    "A",
                    "B",
                    "C",
                    "D",
                    "E"
                ]
            }
        }

    elif count_num == 0 and (content=="A" or content =="B" or content=="C" or content=="D" or content=="E"): #최종 추천
        content = ABCDE_dict[content]
        point_dict[a_tag] = content

        for line in lines:
            for a_tag in list(point_dict.keys()):
                if a_tag in line['특징']:
                    line['점수'] += point_dict[a_tag]

        tag_list.remove(a_tag)

        max_point = 0
        for line in lines:
            if line['점수'] > max_point:
                max_point = line['점수']

        if max_point == 0:
            text = "원하는 tag가 발견되지 않았습니다\n"+"드시고 싶은 것이 아예 없으신가요?"
        else:
            for line in lines:
                if line['점수'] == max_point:
                    text = "{} : {}\n".format(line['음식점'], line['주소'])
                    text += "========================================"
        text += "원하는 키워드를 입력해주세요\n"+"ex) 영통, 안양 고기, 경주 한식\n"+"지역명은 입력 필수입니다"

        # 초기화
        count_num = -1
        tag_set = set()
        tag_list = []
        point_dict = dict()
        lines = []
        a_tag = str()
        
        response = {
            "message": {
                "text": text
            }


        }

    else :
        key_word = content
        key_word = key_word.replace(' ', '+')

        with requests.Session() as Session:

            res_obj = Session.get("https://www.diningcode.com/list.php?query=" + key_word)
            soup = BeautifulSoup(res_obj.text, "html.parser")
            f = open("DATA.txt", "w")

            list_1 = soup.select(".btxt")  # 음식점 list
            del list_1[0]  # 광고 제거

            list_2 = soup.select(".stxt")  # 음식 list
            del list_2[0]  # 광고 제거

            list_3_4 = soup.select(".ctxt")  # 특징,주소 list
            del list_3_4[0:2]  # 광고 제거

            list_3 = []  # 특징 list, 주소 list 분리
            list_4 = []
            num = 1
            for elem in list_3_4:
                elem = elem.text
                if (num % 2) == 0:
                    list_4.append(elem)
                else:
                    list_3.append(elem)
                num += 1

            for i in range(len(list_1)):
                f.write("{}@".format(list_1[i].text[list_1[i].text.find(".") + 2:]))  # 음식점 작성

                f.write("{}@".format(list_2[i].text))  # 음식 작성

                f.write("{}@".format(list_3[i]))  # 특징 작성

                f.write("{}\n".format(list_4[i]))  # 주소 작성

            # 검색된 것이 10개 이상인 경우 추가적으로 크롤링
            var = soup.select_one(".stit")
            num = var.text[:var.text.find("곳")]
            num = int(num.replace(',', ''))
            page = ceil(num / 10)
            if page > 4:
                page = 4

            page_now = 2
            while page_now <= page:  # 10개씩 크롤링
                res_obj = Session.post("https://www.diningcode.com/2018/ajax/list.php",
                                       data={"query": key_word, "page": str(page_now), "chunk": "10"})
                soup = BeautifulSoup(res_obj.text, "html.parser")

                list_1 = soup.select(".btxt")  # 음식점 list
                del list_1[0]  # 광고 제거

                list_2 = soup.select(".stxt")  # 음식 list
                del list_2[0]  # 광고 제거

                list_3_4 = soup.select(".ctxt")  # 특징,주소 list
                del list_3_4[0:2]  # 광고 제거

                list_3 = []  # 특징 list, 주소 list 분리
                list_4 = []
                num = 1
                for elem in list_3_4:
                    elem = elem.text
                    if (num % 2) == 0:
                        list_4.append(elem)
                    else:
                        list_3.append(elem)
                    num += 1

                for i in range(len(list_1)):
                    f.write("{}@".format(list_1[i].text[list_1[i].text.find(".") + 2:]))  # 음식점 작성

                    f.write("{}@".format(list_2[i].text))  # 음식 작성

                    f.write("{}@".format(list_3[i]))  # 특징 작성

                    f.write("{}\n".format(list_4[i]))  # 주소 작성

                page_now += 1

            f.close()

            # dict로 변환
        f = open("DATA.txt", "r")
        liness = f.readlines()
        for i in range(len(liness)):
            line = str(liness[i])
            line = line.strip()
            line = line.split('@')

            list_food = line[1].split(',')
            for j in range(len(list_food)):
                list_food[j] = list_food[j].strip()

            list_tag = line[2].split(',')
            for k in range(len(list_tag)):
                list_tag[k] = list_tag[k].strip()

            lines.append({"번호": i, "음식점": line[0], "음식": list_food, "특징": list_tag, "주소": line[3], "점수":0})
        f.close()

        # 태그 set 만들기
        for elem_dict in lines:
            for a_tag in elem_dict['특징']:
                tag_set.add(a_tag)

        
        text = "{}개의 태그가 발견되었습니다.\n".format(len(tag_set)) + "몇 개의 태그를 평가하시겠습니까?"
        #text = "응답 확인이 되었습니다! 몇 개의 태그를 평가하시겠습니까?"
        response = {
            "message": {
                "text": text
            }
        }

    response = json.dumps(response, ensure_ascii=False)
    return response

if __name__ == "__main__":
    app.run(port=5500)