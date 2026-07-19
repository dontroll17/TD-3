import json
import requests
import mido
import time
import random

# ИМПОРТИРУЕМ МАТЕМАТИЧЕСКОЕ ЯДРО ON TEST NOW!!!!
from input.py import calculate_19tet_pitch_bend, MIDI_PORT_NAME, BASE_NOTE # type: ignore

# ==============================================================================
# НАСТРОЙКИ ИНТЕРФЕЙСОВ
# ==============================================================================
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "qwen2.5:0.5b"  # Радикально экономит VRAM (~1 Гб) и выдает бешеную скорость

# Скорость воспроизведения токенов (интервал между шагами секвенсора)
BPM = 135
STEP_TIME = 60.0 / BPM / 4.0  # Длительность 16-й ноты

# ==============================================================================
# РАБОТА С СЫРЫМ ПОТОКОМ OLLAMA
# ==============================================================================
def parse_and_play_stream(prompt, port):
    """
    Отправляет промпт в Ollama и парсит входящие токены на лету,
    превращая их в физический звук TD-3 без задержек.
    """
    # Формируем тело запроса для Ollama API. 
    # Включаем raw=True, чтобы отключить шаблонные рамки ответов и вызывать больше багов.
    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "raw": True,
        "stream": True,  # ВКЛЮЧАЕМ СТРИМИНГ ТОКЕНОВ
        "options": {
            "temperature": 1.7,     # Выкручиваем хаос и нестабильность модели
            "top_k": 100,
            "max_tokens": 64        # Ограничиваем длину музыкальной фразы
        }
    }

    print(f"\n📡 Отправка промпта в {MODEL_NAME}... Ожидание потока глитчей...")

    try:
        # Делаем потоковый POST-запрос к локальной нейросети
        response = requests.post(OLLAMA_URL, json=payload, stream=True)
        response.raise_for_status()

        # Читаем ответ построчно по мере того, как нейросеть рождает токены
        for line in response.iter_lines():
            if line:
                # Декодируем входящую JSON-строку от Ollama
                data = json.loads(line.decode('utf-8'))
                
                # ХИТРОСТЬ: В Ollama API сырой внутренний ID токена в явном виде 
                # может не отдаваться, поэтому мы берем хэш или ординал от сырого текста куска.
                # Но если вы используете кастомную сборку или vLLM, там есть прямое поле 'token_id'.
                # Сделаем универсальный и стабильный глитч-маппинг текста в число:
                token_text = data.get("response", "")
                if not token_text:
                    continue
                
                # Генерируем уникальное числовое зерно из куска текста (даже из одного символа/бага)
                token_id = sum(ord(char) for char in token_text) * 1337
                
                # Выводим в консоль для визуализации перформанса
                print(f"Токен: '{token_text.encode('utf-8')}' ──> ID: {token_id}")

                # ВЫЗЫВАЕМ НАШЕ 19-ТЕТ ЯДРО ДЛЯ ДАННОГО ТОКЕНА
                execute_midi_step(token_id, port)

    except requests.exceptions.ConnectionError:
        print("Ошибка: Ollama не запущена! Включите Ollama в терминале (`ollama serve`).")
    except Exception as e:
        print(f"Произошла ошибка при парсинге потока: {e}")

def execute_midi_step(token_id, port):
    """
    Принимает ID токена из парсера, рассчитывает микротоны 
    и дергает физические цепи TD-3.
    """
    # 1. Считаем 19-ТЕТ высоту
    step_19_tet = token_id % 38  # Диапазон в две микротональные октавы
    midi_note, pitch_bend_val = calculate_19tet_pitch_bend(step_19_tet)

    # 2. Определяем Акцент (Accent)
    velocity = 127 if token_id % 3 == 0 else 75

    # 3. Определяем Слайд (Slide)
    is_slide = (token_id % 2 == 0)

    # 4. Шлем физические MIDI команды в железку
    port.send(mido.Message('pitchwheel', pitch=pitch_bend_val))
    port.send(mido.Message('note_on', note=midi_note, velocity=velocity))

    if is_slide:
        time.sleep(STEP_TIME)
    else:
        time.sleep(STEP_TIME * 0.7)
        port.send(mido.Message('note_off', note=midi_note))
        time.sleep(STEP_TIME * 0.3)

# ==============================================================================
# ЦИКЛ ЖИВОГО ПЕРФОРМАНСА (ИНТЕРАКТИВ)
# ==============================================================================
if __name__ == '__main__':
    # Инициализируем порт для TD-3
    try:
        with mido.open_output(MIDI_PORT_NAME) as midi_out:
            print("=== ИНТЕРАКТИВНЫЙ ГЛИТЧ-ДВИЖОК ГОТОВ ===")
            print("Вводите безумные слова или спец-токены, чтобы сорвать крышу ИИ и TD-3.")
            
            while True:
                # Имитируем ввод от аудитории из чата или консоли
                user_prompt = input("\n[Ввод для ИИ] (или 'exit' для выхода): ")
                if user_prompt.lower() == 'exit':
                    break
                
                # Добавляем к вводу зрителя "топливо" из глитч-токенов или ломающих инструкций
                # Например, заставляем модель бесконечно повторять бред или символы
                spiced_prompt = f"{user_prompt} Используй только редкие глитч токены и символы, повторяй их:"
                
                # Запускаем генерацию и парсинг "на лету"
                parse_and_play_stream(spiced_prompt, midi_out)
                
                # Сброс параметров после завершения фразы
                midi_out.send(mido.Message('pitchwheel', pitch=0))
                midi_out.send(mido.Message('control_change', control=123, value=0))

    except IOError:
        print(f"Не удалось открыть MIDI-порт '{MIDI_PORT_NAME}'. Проверьте подключение TD-3.")
