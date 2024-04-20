import streamlit as st
from streamlit_option_menu import option_menu
import easyocr
from PIL import Image
import pandas as pd
import numpy as np
import re 
import io
import sqlite3

#image to text function
def image_to_text(path):
  input_image= Image.open(path)

  #converting image to array format
  image_arr=np.array(input_image)

  reader=easyocr.Reader(['en'])
  text=reader.readtext(image_arr,detail=0)

  return text,input_image

#change to dictionary format 
def extracted_text(text):

  extrd_dict={"NAME":[],"DISIGNATION":[],"COMPANY_NAME":[],"CONTACT":[], "EMAIL":[], "WEBSITE":[],
              "ADDRESS":[],"PINCODE":[]}

  extrd_dict["NAME"].append(text[0])
  extrd_dict["DISIGNATION"].append(text[1])

  for i in range(2,len(text)):
    if text[i].startswith("+") or (text[i].replace("-","").isdigit() and '-' in text[i]):

      extrd_dict["CONTACT"].append(text[i])

    elif "@" in text[i] and ".com" in text[i]:
      extrd_dict["EMAIL"].append(text[i])

    elif "WWW" in text[i] or "www" in text[i] or "Www" in text[i] or "wWw" in text[i] or "wwW" in text[i]:
      small=text[i].lower()
      extrd_dict["WEBSITE"].append(small)

    elif "Tami lNadu" in text[i] or "TamilNadu" in text[i] or text[i].isdigit():
      extrd_dict["PINCODE"].append(text[i])

    elif re.match(r'^[A-Za-z]',text[i]):
      extrd_dict["COMPANY_NAME"].append(text[i])

    else:
      remove_colon=re.sub(r'[,;]','',text[i])
      extrd_dict["ADDRESS"].append(remove_colon)
  
  for key,value in extrd_dict.items():
    if len(value)>0:
      concadenate=" ".join(value)
      extrd_dict[key] = [concadenate]

    else:
      value = "NA"
      extrd_dict[key] = [value]

  return extrd_dict



#streamlit part 

st.set_page_config(layout="wide")
st.markdown("<h1 style='text-align: center;'>EXTRACTING BUSINESS CARD DATA WITH 'OCR'</h1>", unsafe_allow_html=True)


select = option_menu(None , ["INSTRUICTIONS & HOME", "Data Extractionn & SQL upload", "Modify & delete"],
                     icons=['house','kanban','book'],
                     menu_icon="cast",default_index=0,
                     orientation='horizontal',                                    #this part suits further experimnet
                     styles={
                         "container":{"padding":"5!important","background-color":"#fa34xx"},
                         "icon":{"color":"orange","font-size":"25px"},
                         "nav-link":{"font-size":"16px","text-align":"left","margin":"0px","--hover-color":"#867"},
                         "nav-link-selected":{"background-color":"#02tt21"}
                        
                     })


if select == "INSTRUICTIONS & HOME":
    pass

elif select == "Data Extractionn & SQL upload":
    img = st.file_uploader("Upload the image",type=["png","jpg","jpeg"])

    if img is not None:
      st.image(img,width=300)

      text_image,input_image= image_to_text(img)

      text_dict=extracted_text(text_image)

      if text_dict:
          st.success("Text extracted successfully")

      df = pd.DataFrame(text_dict)

       #converting image to bytes 

      image_bytes = io.BytesIO()
      input_image.save(image_bytes, format="PNG")

      Image_data = image_bytes.getvalue()

      #creating Dicgtionary 

      data = {"IMAGE":[Image_data]}

      df_1= pd.DataFrame(data)

      cocat_df= pd.concat([df,df_1],axis=1)

      st.dataframe(cocat_df)

      button_1 = st.button("Save to database",use_container_width=200)

      if button_1:
        mydb = sqlite3.connect("biscardx.db")
        cursor = mydb.cursor()

        #table creation
        create_table_query = '''create table if not exists bizcard_details(name varchar(225),
                                                                            designation varchar(225),
                                                                            company_name varchar(225),
                                                                            contact varchar(225),
                                                                            email varchar(225),
                                                                            website text,
                                                                            address text,
                                                                            pincode varchar(225),
                                                                            image text )'''

        cursor.execute(create_table_query)
        mydb.commit()

        #insert query 

        insert_query = '''insert into bizcard_details(name, designation, company_name, contact, email, website, address, pincode, 
                                                      image)
                                                        
                                                        values(?,?,?,?,?,?,?,?,?)'''
        datas = cocat_df.values.tolist()[0]
        cursor.execute(insert_query,datas)
        mydb.commit()
        st.success("save successfully")

    #option part in code 
    method = st.multiselect("Select the Method",["preview","Modify"]) 

    if "preview" in method:
      
      mydb = sqlite3.connect("biscardx.db")
      cursor = mydb.cursor()
      
      #select query 
      select_query = "select * from bizcard_details"

      cursor.execute(select_query)
      table=cursor.fetchall()
      mydb.commit()

      table_df=pd.DataFrame(table,columns=("Name","designation","company_name","contact","email","website","address","pincode","image"))
      st.dataframe(table_df)

    elif "Modify" in method:
        mydb = sqlite3.connect("biscardx.db")
        cursor = mydb.cursor()
        
        #select query 
        select_query = "select * from bizcard_details"

        cursor.execute(select_query)
        table=cursor.fetchall()
        mydb.commit()

        table_df=pd.DataFrame(table,columns=("Name","designation","company_name","contact","email","website","address","pincode","image"))
        st.dataframe(table_df)
       
        col1,col2=st.columns(2)
        with col1:
           
           selected_name = st.selectbox("select the name", table_df["Name"])

        df_3= table_df[table_df["Name"]==selected_name]


        df_4= df_3.copy()


        col1,col2,col3=st.columns(3)
        with col1:
           
           no_name = st.text_input("Name",df_3["Name"].unique()[0])
           no_desi = st.text_input("designation",df_3["designation"].unique()[0])
           no_comp = st.text_input("company_name",df_3["company_name"].unique()[0])
           
           df_4["Name"] = no_name
           df_4["designation"] = no_desi
           df_4["company_name"] = no_comp
           

        with col2:
           no_contact = st.text_input("contact",df_3["contact"].unique()[0])
           no_email = st.text_input("email",df_3["email"].unique()[0])
           no_web = st.text_input("website",df_3["website"].unique()[0])

           df_4["contact"] = no_contact
           df_4["email"] = no_email
           df_4["website"] = no_web

        with col3:
           no_address = st.text_input("address",df_3["address"].unique()[0])
           no_pincode = st.text_input("pincode",df_3["pincode"].unique()[0])
           no_img = st.text_input("image",df_3["image"].unique()[0])

           df_4["address"] = no_address
           df_4["pincode"] = no_pincode
           df_4["image"] = no_img

        
        st.dataframe(df_4)

        col1,col2= st.columns(2)
        
        with col1:
           button_3 = st.button("Modify",use_container_width= True)

        if button_3:
          mydb = sqlite3.connect("biscardx.db")
          cursor = mydb.cursor()

          cursor.execute(f"Delete from bizcard_details where name = '{selected_name}'")
          mydb.commit()

          #insert query 

          insert_query = '''insert into bizcard_details(Name, designation, company_name, contact, email, website, address, pincode, 
                                                        image)
                                                          
                                                          values(?,?,?,?,?,?,?,?,?)'''
          datas = df_4.values.tolist()[0]
          cursor.execute(insert_query,datas)
          mydb.commit() 
          st.success("modified successfully")



elif select == "Modify & delete":
    
    mydb = sqlite3.connect("biscardx.db")
    cursor = mydb.cursor()

    col1,col2=st.columns(2)
    with col1:

      select_query = "select Name from bizcard_details"

      cursor.execute(select_query)
      table=cursor.fetchall()
      mydb.commit()

      names = []

      for i in table:
          names.append(i[0])

      name_select=st.selectbox("Select the name",names)

    with col2:

      select_query_2 = f"select designation from bizcard_details where name = '{name_select}'"         ############

      cursor.execute(select_query_2)
      table_2=cursor.fetchall()
      mydb.commit()

      designations = []

      for j in table_2:
          designations.append(j[0])

      desig_select=st.selectbox("Select the designation",designations)

    if name_select and desig_select:
       
       col1,col2,col3=st.columns(3)

       with col1:
          st.write(f"Selected Name : {name_select}")
          st.write("")
          st.write("")
          st.write("")
          st.write(f"Selected Designation: {desig_select}") 

       with col2:
          st.write("")
          st.write("")
          st.write("")
          st.write("")

          remove = st.button("delete")

          if remove:
             cursor.execute(f"delete from bizcard_details where Name = '{name_select}' and designation = '{desig_select}'")
             mydb.commit()

             st.warning("DELETED")