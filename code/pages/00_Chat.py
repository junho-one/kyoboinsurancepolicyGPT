import re
import streamlit as st
from streamlit_chat_kyobo import message
from utilities.helper import LLMHelper
from datetime import datetime
import ast
import hashlib
import logging

introductory_phrase = """안녕하세요. 저는 교보생명의 보험약관을 설명해 드리는 교보 챗GPT입니다. 설명이 필요하신 보험약관 문의가 있으신가요??

보다 정확한 내용을 파악하기 위해서 궁금하신 보험명을 포함하여 질문해주시고
보험 가입하신 고객이라면 가입날짜까지 알려주시면 더욱 더 정확한 답변을 할 수가 있습니다.
(날짜를 모르시면 최신약관으로 설명됩니다.)
"""
reinformation_phrase = """상품명과 가입년도를 알려주세요~
(예: 1992년도에 가입했고 종신보험이야)
"""

#화면구성
st.set_page_config(layout="wide")

        
llm_helper = LLMHelper()

subscription_info = dict()
def clear_text_input():
    if chk_subscription_info(subscription_info):
        st.session_state['question'] = st.session_state['input']
        st.session_state['input'] = ""
    else :
        st.session_state['subscription_question'] = st.session_state['input']    
        st.session_state['input'] = ""

def clear_chat_data():    
    st.session_state.clear()
    init_sessionState()

def chage_synonym(question):
    print("테스트 테스트으")
    for idx, row in synonym_df.iterrows():
        question = re.sub("|".join(row.synonymList), row.title, question)
    return question   


# 데이터 유효성 검사
def chk_subscription_info(subscription_info):
    if not st.session_state['name'] or len(st.session_state['name']) < 2 or st.session_state['name'] == 'no' :
        return False
    
    now = datetime.now()
    if not st.session_state['year'] or not len(st.session_state['year'])==4 :
        st.session_state['year'] = str(now.year)
        st.session_state['month'] = '0' + str(now.month) if now.month <10 else str(now.month)        
        return True
    else :
        # 년도만 있을 경우 1월을 더해줌
        if not st.session_state['month'] or not len(st.session_state['month'])==2:
            st.session_state['month'] = '0' + str(now.month) if now.month <10 else str(now.month)        
        return True
    

def _sell_date(dates):
    from dateutil.parser import parse

    start = parse(dates[0]).strftime("%Y년 %m월 %d일")

# load synonym data
synonym_df = llm_helper.vector_store.get_synonym_results()


# Initialize chat history
if 'question' not in st.session_state:
    st.session_state['question'] = []
    #임시 질문
    st.session_state['temp_question'] = []
if 'chat_history' not in st.session_state:
    st.session_state['chat_history'] = []
if 'source_documents' not in st.session_state:
    st.session_state['source_documents'] = []
if 'subscription_question' not in st.session_state:
    st.session_state['subscription_question'] = []
    st.session_state['year'] = ""
    st.session_state['name'] = ""
if 'subscription_history' not in st.session_state:
    st.session_state['subscription_history']  = []
    

#값 초기화
# chatHistory에 질문이 추가되면 꼬일수가 있어서 history에 추가 안하고 message로 표출해야 됌
if st.session_state['subscription_question']:
    question, subscription_info = llm_helper.get_extract_entity(st.session_state['subscription_question'])
    st.session_state['name'] =subscription_info['subscriptionName']
    st.session_state['date'] =subscription_info['subscriptionDate']
   # st.session_state['chat_history'].append((question, result))
    if(chk_subscription_info(subscription_info)):
      #  st.session_state['subscription_history'].append((st.session_state['subscription_question'] ,"상품명과 가입년도가 인식되었습니다. 질문해주세요 {0} {1} ".format( st.session_state['name'] ,st.session_state['date'] ) )  )
       
        st.session_state['subscription_question'] = []
        # 기간인식 전 질문했던 것이 있으면 재질문
        if st.session_state['temp_question']:
            st.session_state['question'] = st.session_state['temp_question']
            st.session_state['temp_question'] ="" 
        else :
            st.session_state['subscription_history'].append((st.session_state['subscription_question'] ,"상품명과 가입년도가 알아냈습니다. 질문해주세요 ") )    
    else :
        st.session_state['subscription_history'].append(( st.session_state['subscription_question'] ,reinformation_phrase )  )
        #날짜 없이 질문 했으면 임시질문에 저장 
        st.session_state['temp_question'] = st.session_state['subscription_question']


if st.session_state['question']:

def get_hashkey_insurance_date(insurance_name, insurance_date):
    similar_insurance = llm_helper.vector_store.similarity_search_with_score_insurance(insurance_name, "*", index_name="insurance-index", k=4)
    best_insurance = similar_insurance.docs[0]
    
    date_list = [str(i) for i in ast.literal_eval(best_insurance.date)]
    date_list.append("현재")
    
    candidate_date = []
    for idx in range(1, len(date_list)):
        candidate_date.append((date_list[idx-1], date_list[idx]))

    insurance_key = best_insurance.insurance
    date_key = None
    for start, end in candidate_date:
        if start <= insurance_date < end:
            date_key = start
            sell_date = (start, end)
    
    if date_key is None:
        date_key = candidate_date[-1][0]
        sell_date = candidate_date[-1]

    candidate_date = date_list[:-1]

    search_key = insurance_key + ":" + date_key
    hash_key = hashlib.sha1(search_key.encode('utf-8')).hexdigest()    

    candidate_insurance = [ins.insurance for ins in similar_insurance.docs[1:]]        

    sell_date = _sell_date(sell_date)
    candidate_date = _revised_date(candidate_date)
    candidate_insurance = _candidate_insurance(candidate_insurance)


    return hash_key, insurance_key, sell_date, candidate_date, candidate_insurance


# load synonym data
synonym_df = llm_helper.vector_store.get_synonym_results()

# Initialize chat history
def init_sessionState():
    if 'question' not in st.session_state:
        st.session_state['question'] = []

    if 'chat_history' not in st.session_state:
        st.session_state['chat_history'] = []
    if 'source_documents' not in st.session_state:
        st.session_state['source_documents'] = []
    if 'subscription_question' not in st.session_state:
        st.session_state['subscription_question'] = []
        st.session_state['year'] = ""
        st.session_state['name'] = ""
        st.session_state['month'] = ""    
        st.session_state['date'] = ""    
        #임시 질문
        st.session_state['temp_question'] = []        
    if 'subscription_history' not in st.session_state:
        st.session_state['subscription_history']  = []
    
init_sessionState() 

#값 초기화
# chatHistory에 질문이 추가되면 꼬일수가 있어서 history에 추가 안하고 message로 표출해야 됌
if st.session_state['subscription_question']:
    question, subscription_info = llm_helper.get_extract_entity(st.session_state['subscription_question'])
    st.session_state['name'] =subscription_info['subscriptionName']
    st.session_state['year'] =subscription_info['subscriptionYear']
    st.session_state['month'] = subscription_info['subscriptionMonth'] 
   # st.session_state['chat_history'].append((question, result))
    if(chk_subscription_info(subscription_info)):
      #  st.session_state['subscription_history'].append((st.session_state['subscription_question'] ,"상품명과 가입년도가 인식되었습니다. 질문해주세요 {0} {1} ".format( st.session_state['name'] ,st.session_state['date'] ) )  )
       
        # 기간인식 전 질문했던 것이 있으면 재질문
        if st.session_state['temp_question']:
            # st.session_state['question'] = st.session_state['temp_question']
          #  st.session_state['subscription_history'].append((st.session_state['subscription_question'], "상품명과 가입년도를 알아냈습니다. 질문해주세요 "))
            hash_key, insurance_key, sell_date, candidate_date, candidate_insurance = get_hashkey_insurance_date(st.session_state['name'], st.session_state['date'])
            # all_question = ". ".join(st.session_state['temp_question'])
            question, result, _, sources = llm_helper.get_semantic_answer_lang_chain(st.session_state['temp_question'], "", hash_key)

            if sources != '':
                logging.info("subscription histroy 끝")
                logging.info(sources)
                logging.info(_)
          #      st.session_state['chat_history'].append(( st.session_state['subscription_question'], result))
            st.session_state['subscription_history'].append(( st.session_state['subscription_question'],""))
            # else:
            #     st.session_state['subscription_history'].append((st.session_state['subscription_question'] ,"상품명과 가입년도가 알아냈습니다. 질문해주세요 ") )
        # 기간인식이 없었으면 
                #st.session_state['temp_question'] = []
        else :
            st.session_state['subscription_history'].append((st.session_state['subscription_question'] ,"상품명과 가입년도가 알아냈습니다. 질문해주세요 ") )    
    else :
        st.session_state['subscription_history'].append(( st.session_state['subscription_question'] ,reinformation_phrase )  )
        #날짜 없이 질문 했으면 임시질문에 저장 
        st.session_state['temp_question'] = st.session_state['subscription_question']
        # st.session_state['temp_question'].append(st.session_state['subscription_question'])

    st.session_state['subscription_question'] = []

if st.session_state['question'] or(st.session_state['temp_question'] and chk_subscription_info(subscription_info) ) :

    # 질문 : 소멸시효에 대해 알려줘
   # st.session_state['name'] = "(무)실손의료비보험(갱신형)3"
   # st.session_state['date'] = '2021년 3월'
    
    # 질문 : 
    # st.session_state['name'] = "생명보험"
    # st.session_state['date'] = '2021년 3월'
    
    
    st.session_state['date'] =  st.session_state['year'] + "." + st.session_state['month'] 
    hash_key, insurance_key, sell_date, candidate_date, candidate_insurance = get_hashkey_insurance_date(st.session_state['name'], st.session_state['date'])

    intro = f"현재 답변은 <{sell_date}> 까지 판매된 <{insurance_key}> 약관 기준으로 설명할게요. \n\n"
    outro = "\n\n상세한 내용은 상품설명서를 반드시 확인해보시기 바랍니다."

    candidate_info = f"""\n\n
                        입력하신 정보와 유사한 보험 상품은 : {candidate_insurance} 가 있습니다."""
    
    if st.session_state['temp_question']:
        question, result, _, sources = llm_helper.get_semantic_answer_lang_chain(st.session_state['temp_question'], "", hash_key)

    else :
         question, result, _, sources = llm_helper.get_semantic_answer_lang_chain(st.session_state['question'], "", hash_key)
         
    if sources == '':
        logging.info("no sources")
        logging.info(sources)
        logging.info(_)
        result = result + "\n\n 약관답변 아님"
    else:
        logging.info("yes sources")
        logging.info(sources)
        logging.info(_)
        result = intro + result + outro + candidate_info
    if st.session_state['temp_question']:    
        st.session_state['chat_history'].append(("", result))
        st.session_state['temp_question'] = []
    else :
        st.session_state['chat_history'].append((question, result))    
    st.session_state['source_documents'].append(sources)
    st.session_state['question'] = []


message(introductory_phrase)
#소개문구
# message(introductory_phrase, logo="C:\\chatgpt\\code\\EmbeddingsRedis\\code\\images\\")
if st.session_state['subscription_history']:
    for i in range(0, len(st.session_state['subscription_history']),1  ):
        if st.session_state['subscription_history'][i][0] : message(st.session_state['subscription_history'][i][0], is_user=True, key='sub' +str(i) + '_user')
        if st.session_state['subscription_history'][i][1] : message(st.session_state['subscription_history'][i][1], key= 'sub'+str(i))
    
if st.session_state['chat_history']:
    for i in  range(0, len(st.session_state['chat_history']), 1):
        if st.session_state['chat_history'][i][0] : message(st.session_state['chat_history'][i][0], is_user=True, key= str(i) + '_user')
        if st.session_state['chat_history'][i][1] : message(st.session_state['chat_history'][i][1], key=str(i))

 
# Chat 
st.text_input("You: ", placeholder="type your question", key="input", on_change=clear_text_input)
clear_chat = st.button("Clear chat", key="clear_chat", on_click=clear_chat_data)
 
 
  #채팅창 아래로 바꾸고 표출순서 변경
  #   for i in range(0, 1, len(st.session_state['chat_history'])):
   #     message(st.session_state['chat_history'][i][0], is_user=True, key=str(i) + '_user')
    #    message(st.session_state['chat_history'][i][1], key=str(i))