import streamlit as st
from PIL import Image
import requests
import pandas as pd
import base64
from fake_useragent import UserAgent

st.set_page_config(page_title='Co-Win: Covid-19 Vaccination Tracker', page_icon='💉', layout = 'centered', initial_sidebar_state = 'expanded')

ua = UserAgent()
header = {'User-Agent': 'Mozilla/5.0'}
state_reponse = requests.get('https://cdn-api.co-vin.in/api/v2/admin/location/states', headers=header)
print("\n\n ==================== \n\n")
print(state_response)
print("\n\n ==================== \n\n")
states = state_reponse.json()
states_dict = {}
states_dict['0'] = 'Select State'
for i in states['states']:
    states_dict[i['state_id']] = i['state_name']
states_list = list(states_dict.values())

def get_key(dict, val):
    for key, value in dict.items():
        if val == value:
            return key
    return "key doesn't exist"

def get_table_download_link(df, filename, text):
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    return f'<a href="data:file/csv;base64,{b64}" download="{filename}">{text}</a>'

def get_districts(key):
    district_reponse = requests.get('https://cdn-api.co-vin.in/api/v2/admin/location/districts/'+key, headers=header)
    districts = district_reponse.json()
    districts_dict = {}
    for i in districts['districts']:
        districts_dict[i['district_id']] = i['district_name']
    return districts_dict

st.markdown("<h1 style='text-align: center; color: #2970ff; font-size: 5em;'> CoWin 💉 </h1>", unsafe_allow_html=True)
st.markdown("<h3 style='text-align: center; color: #2970ff;'> Covid-19 Vaccination Tracker for India </h3>", unsafe_allow_html=True)
st.markdown("<h5 style='text-align: center; color: #eb5e42;'> Developed with ♥ by Polybit & TechNinja </h5>", unsafe_allow_html=True)
st.markdown("<h1></h1>", unsafe_allow_html=True)
st.markdown("<h1></h1>", unsafe_allow_html=True)

col1, col2 = st.columns([1,1])

col1.markdown("<h2 style='text-align: center; color: #2970ff;'> Step 1 </h3>", unsafe_allow_html=True)
col1.markdown("<h5 style='text-align: center;'> Location and Date </h5>", unsafe_allow_html=True)

col2.markdown("<h2 style='text-align: center; color: #2970ff;'> Step 2 </h3>", unsafe_allow_html=True)
col2.markdown("<h5 style='text-align: center;'> Vaccine Type </h5>", unsafe_allow_html=True)

location_choice = col1.radio("Choose location by", ["...", "District", "PIN Code"])
if location_choice == "District":
    states_list.remove("Daman and Diu")
    # Select States
    states_box = col1.selectbox("Select State", states_list)
    if states_box == 'Select State':
        col1.warning("Please select a state to continue...")
    else:
        state_index = states_list.index(states_box)
        district_dict = get_districts(str(state_index))
        district_list = list(district_dict.values())
        # Select Districts
        district_list.insert(0, 'Select District')
        district_box = col1.selectbox("Select District", district_list)
        if district_box == 'Select District':
            col1.warning("Please select a district to continue...")
        else:
            dist_key = get_key(district_dict, district_box)

            vac_date = col1.date_input("Select Date (Optional)")
            vac_date = str(vac_date).split('-')
            new_date = vac_date[2]+'-'+vac_date[1]+'-'+vac_date[0]

            age = col2.select_slider("Choose Age Group", ["Only 15-18", "15-18/18+", "Only 18+"], "15-18/18+")
            age_val = 0

            vaccine = col2.selectbox("Vaccine Type", ["Covishield", "Covaxin", "Sputnik V"])
            vaccine_type = ''
            if vaccine == 'Covishield':
                vaccine_type = 'COVISHIELD'
            elif vaccine == 'Covaxin':
                vaccine_type = 'COVAXIN'
            elif vaccine == 'Sputnik V':
                vaccine_type = 'SPUTNIK-V'
            
            fee = col2.select_slider("Choose Fee", ["Free", "Both Free and Paid", "Paid"], "Both Free and Paid")

            if col2.button("Search!"):
                center_response = requests.get(
                    f"https://cdn-api.co-vin.in/api/v2/appointment/sessions/public/calendarByDistrict?district_id={dist_key}&date={new_date}",
                    headers=header)
                centers_data = center_response.json()
                centers = pd.DataFrame(centers_data.get('centers'))

                if centers.empty:
                    st.error("No centers found in this District...")
                else:
                    with st.spinner("Fetching data... Please wait patiently..."):
                        for i in range(50000):
                            pass

                        session_ids = []
                        for j, row in centers.iterrows():
                            session = pd.DataFrame(row['sessions'][0])
                            session['center_id'] = centers.loc[j, 'center_id']
                            session_ids.append(session)

                        sessions = pd.concat(session_ids, ignore_index=True)
                        av_centeres = centers.merge(sessions, on='center_id')

                        if age == '18+':
                            age_val = 18
                            av_centeres = av_centeres[av_centeres['min_age_limit'] == age_val]
                        elif age == '15-18':
                            age_val = 15
                            av_centeres = av_centeres[av_centeres['min_age_limit'] == age_val]
                    
                        av_centeres.drop(
                            columns=['sessions', 'session_id', 'lat', 'block_name', 'long', 'date', 'from', 'to',
                                     'state_name', 'district_name', 'max_age_limit', 'vaccine_fees', 'allow_all_age'],
                                     inplace=True, errors='ignore')
                    
                        av_centeres = av_centeres[av_centeres['vaccine'] == vaccine_type]

                        if fee != 'Both Free and Paid':
                            av_centeres = av_centeres[av_centeres['fee_type'] == fee]
                    
                        new_df = av_centeres.copy()
                        new_df.columns = ['Center_ID', 'Name', 'Address', 'Pincode', 'Fee', 'Availability', 'Minimum Age',
                                         'Vaccine Type', 'Timing', 'Dose 1', 'Dose 2']
                        new_df = new_df[['Center_ID', 'Name', 'Fee', 'Pincode',
                                         'Availability', 'Minimum Age', 'Vaccine Type', 'Timing', 'Address', 'Dose 1',
                                         'Dose 2']]
                        if new_df.empty:
                            st.error("No Center found in this District...")
                        else:
                            st.dataframe(new_df.assign(hack='').set_index('hack'))
                            st.markdown("<h5 style='text-align: center;'> Scroll vertically to view more centers, Scroll horizontally to view all the data in columns. </h5>", unsafe_allow_html=True)
                            st.markdown(get_table_download_link(new_df,
                                        district_box.replace(' ', '_') + '_' + new_date.replace('-', '_') + '.csv',
                                        'Download Report'), unsafe_allow_html=True)
                            href = f'<a href="https://selfregistration.cowin.gov.in/" target="_blank">Book Slot</a>'
                            st.markdown(href, unsafe_allow_html=True)
                            linkjson = f"https://cdn-api.co-vin.in/api/v2/appointment/sessions/public/calendarByDistrict?district_id={dist_key}&date={new_date}"
                            href_2 = f'<p>Some data may be incorrect so <a href="{linkjson}" target="_blank">click here</a> to visit the source API data.</p>'
                            st.markdown(href_2, unsafe_allow_html=True)
elif location_choice == 'PIN Code':
    # Area PIN Code
    area_pin = col1.text_input('Enter your Area Pin-Code Eg.380015')
    if area_pin.strip() == '':
        col1.warning("Please type a PIN Code to continue...")
    else:
        vac_date = col1.date_input("Select Date (Optional)")
        vac_date = str(vac_date).split('-')
        new_date = vac_date[2]+'-'+vac_date[1]+'-'+vac_date[0]

        age = col2.select_slider("Choose Age Group", ["Only 15-18", "15-18/18+", "Only 18+"], "15-18/18+")
        age_val = 0

        vaccine = col2.selectbox("Vaccine Type", ["Covishield", "Covaxin", "Sputnik V"])
        vaccine_type = ''
        if vaccine == 'Covishield':
            vaccine_type = 'COVISHIELD'
        elif vaccine == 'Covaxin':
            vaccine_type = 'COVAXIN'
        elif vaccine == 'Sputnik V':
            vaccine_type = 'SPUTNIK-V'
            
        fee = col2.select_slider("Choose Fee", ["Free", "Both Free and Paid", "Paid"], "Both Free and Paid")

        if col2.button("Search!"):
            center_response = requests.get(
            f"https://cdn-api.co-vin.in/api/v2/appointment/sessions/public/calendarByPin?pincode={area_pin}&date={new_date}",
            headers=header)
            centers_data = center_response.json()
            centers = pd.DataFrame(centers_data.get('centers'))

            if centers.empty:
                st.error("No centers found in or near this PIN Code...")
            else:
                with st.spinner("Fetching data... Please wait patiently..."):
                    for i in range(50000):
                        pass

                    session_ids = []
                    for j, row in centers.iterrows():
                        session = pd.DataFrame(row['sessions'][0])
                        session['center_id'] = centers.loc[j, 'center_id']
                        session_ids.append(session)

                    sessions = pd.concat(session_ids, ignore_index=True)
                    av_centeres = centers.merge(sessions, on='center_id')
                    
                    if age == '18+':
                        age_val = 18
                        av_centeres = av_centeres[av_centeres['min_age_limit'] == age_val]
                    elif age == '15-18':
                        age_val = 15
                        av_centeres = av_centeres[av_centeres['min_age_limit'] == age_val]
                    
                    av_centeres.drop(
                                columns=['sessions', 'session_id', 'lat', 'block_name', 'long', 'date', 'from', 'to', 'state_name',
                                'district_name', 'max_age_limit', 'vaccine_fees', 'allow_all_age'],
                                inplace=True, errors='ignore')
                    
                    av_centeres = av_centeres[av_centeres['vaccine'] == vaccine_type]

                    if fee != 'Both Free and Paid':
                        av_centeres = av_centeres[av_centeres['fee_type'] == fee]
                    
                    new_df = av_centeres.copy()
                    new_df.columns = ['Center_ID', 'Name', 'Address', 'Pincode', 'Fee', 'Availability', 'Minimum Age',
                                    'Vaccine Type', 'Timing', 'Dose 1', 'Dose 2']
                    new_df = new_df[['Center_ID', 'Name', 'Fee', 'Pincode',
                                    'Availability', 'Minimum Age', 'Vaccine Type', 'Timing', 'Address', 'Dose 1', 'Dose 2']]
                        
                    if new_df.empty:
                        st.error("No Center found in or near this PIN Code...")
                    else:
                        st.dataframe(new_df.assign(hack='').set_index('hack'))
                        st.markdown("<h5 style='text-align: center;'> Scroll vertically to view more centers, Scroll horizontally to view all the data in columns. </h5>", unsafe_allow_html=True)
                        st.markdown(get_table_download_link(new_df, area_pin + '_' + new_date.replace('-', '_') + '.csv',
                                    'Download Report'), unsafe_allow_html=True)
                        href = f'<a href="https://selfregistration.cowin.gov.in/" target="_blank">Book Slot</a>'
                        st.markdown(href, unsafe_allow_html=True)
                        linkjson = f"https://cdn-api.co-vin.in/api/v2/appointment/sessions/public/calendarByPin?pincode={area_pin}&date={new_date}"
                        href_2 = f'<p>Some data may be incorrect so <a href="{linkjson}" target="_blank">click here</a> to visit the source API data.</p>'
                        st.markdown(href_2, unsafe_allow_html=True)
