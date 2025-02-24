import os
import json
import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv

# Ładowanie klucza API z pliku .env
load_dotenv()

def is_valid_api_key(api_key):
    try:
        client = OpenAI(api_key=api_key)
        client.models.list()  # Próba dostępu do modeli
        return True
    except Exception:
        return False

# Inicjalizacja stanu sesji
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("Logowanie do Generatora Kolorowanek - LEoNARDo")
    api_key_input = st.text_input("Wprowadź swój klucz OpenAI:", type="password")
    if st.button("Zaloguj"):
        if is_valid_api_key(api_key_input):
            st.session_state.authenticated = True
            st.session_state.api_key = api_key_input
            st.success("Pomyślnie zalogowano!")
            st.rerun()
        else:
            st.error("Nieprawidłowy klucz API. Spróbuj ponownie.")
    st.stop()

# Inicjalizacja klienta OpenAI
client = OpenAI(api_key=st.session_state.api_key)

# Ścieżka do pliku z zapisanymi propozycjami
SAVE_FILE = "coloring_ideas.json"

# Funkcja do zapisywania pomysłów do pliku JSON
def save_ideas(topic, ideas):
    data = {}
    if os.path.exists(SAVE_FILE):
        with open(SAVE_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)
    data[topic] = ideas
    with open(SAVE_FILE, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)

# Funkcja do ładowania zapisanych pomysłów
def load_saved_ideas():
    if os.path.exists(SAVE_FILE):
        with open(SAVE_FILE, "r", encoding="utf-8") as file:
            return json.load(file)
    return {}

# Funkcja do usuwania zapisanych pomysłów
def delete_saved_idea(topic):
    if os.path.exists(SAVE_FILE):
        with open(SAVE_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)
        if topic in data:
            del data[topic]
            with open(SAVE_FILE, "w", encoding="utf-8") as file:
                json.dump(data, file, ensure_ascii=False, indent=4)

# Funkcja do generowania pomysłów na kolorowanki (w języku polskim)
def generate_coloring_book_ideas(topic):
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "Jesteś kreatywnym asystentem, który generuje pomysły na kolorowanki dla dzieci. Odpowiadaj tylko w języku polskim."},
            {"role": "user", "content": f"Wygeneruj 10 prostych i zabawnych pomysłów na kolorowanki związane z tematem: {topic}. Pomysły powinny być odpowiednie dla dzieci."}
        ]
    )
    ideas = response.choices[0].message.content.strip().split("\n")
    return ideas

# Funkcja do generowania obrazów kolorowanek
def generate_coloring_book_images(idea, num_images):
    images = []
    for _ in range(num_images):
        response = client.images.generate(
            model="dall-e-3",
            prompt=f"Prosty czarno-biały rysunek dla dziecięcej kolorowanki: {idea}",
            n=1,
            size="1024x1024",
            quality="standard"
        )
        images.append(response.data[0].url)
    return images

# Interfejs użytkownika w Streamlit
st.title("LEgitoNARDo - Generator Kolorowanek dla Dzieci")

# Inicjalizacja stanu sesji
if "ideas" not in st.session_state:
    st.session_state.ideas = None
if "selected_idea" not in st.session_state:
    st.session_state.selected_idea = None

# Wczytanie zapisanych pomysłów
saved_ideas = load_saved_ideas()

# Opcja wyboru zapisanego tematu
if saved_ideas:
    selected_saved_topic = st.selectbox("Wybierz zapisany temat:", ["Wybierz..."] + list(saved_ideas.keys()))
    if selected_saved_topic != "Wybierz...":
        st.session_state.ideas = saved_ideas[selected_saved_topic]
        if st.button("Usuń zapisany temat"):
            delete_saved_idea(selected_saved_topic)
            st.success(f"Temat '{selected_saved_topic}' został usunięty.")
            st.rerun()

# Input od użytkownika: temat przewodni
topic = st.text_input("Lub podaj temat przewodni kolorowanki:")

if topic and st.button("Pokaż Pomysły"):
    # Generowanie 10 pomysłów na kolorowanki
    with st.spinner("Generowanie pomysłów..."):
        st.session_state.ideas = generate_coloring_book_ideas(topic)
        save_ideas(topic, st.session_state.ideas)  # Zapisanie pomysłów
    st.success("Pomysły wygenerowane i zapisane pomyślnie!")

# Wyświetlenie pomysłów i umożliwienie wyboru
if st.session_state.ideas:
    st.session_state.selected_idea = st.selectbox("Wybierz pomysł na kolorowankę:", st.session_state.ideas)

    # Input od użytkownika: liczba rysunków do wygenerowania
    num_images = st.number_input("Wybierz ilość rysunków do wygenerowania:", min_value=1, max_value=10, value=1)

    if st.button("Stwórz Kolorowanki"):
        if st.session_state.selected_idea and num_images:
            with st.spinner("Generowanie obrazów..."):
                images = generate_coloring_book_images(st.session_state.selected_idea, num_images)
            
            st.success("Kolorowanki wygenerowane pomyślnie!")
            
            # Wyświetlenie i opcja pobrania obrazów
            for i, image_url in enumerate(images):
                st.write(f"**Kolorowanka {i+1}:** {st.session_state.selected_idea}")
                st.image(image_url, caption=f"Kolorowanka {i+1}")
                st.markdown(f"[Pobierz obraz {i+1}]({image_url})", unsafe_allow_html=True)
        else:
            st.error("Proszę wybrać pomysł i liczbę rysunków.")
else:
    st.info("Wprowadź temat przewodni i kliknij 'Generuj Pomysły', aby rozpocząć.")
