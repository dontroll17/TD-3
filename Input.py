import time
import random
import mido

# ==============================================================================
# НАСТРОЙКИ ПОДКЛЮЧЕНИЯ И СТРОЯ
# ==============================================================================
# Посмотрите точное имя вашего MIDI-порта для TD-3 через: mido.get_output_names()
MIDI_PORT_NAME = 'Ваш_MIDI_Порт_TD-3' 
BASE_NOTE = 36  # До малой октавы. Оптимальный басовый регистр для TD-3

CENTS_PER_STEP_19TET = 1200.0 / 19.0  # ~63.158 центов на один шаг
PITCH_BEND_RANGE_CENTS = 200.0        # Аппаратный диапазон TD-3 (±2 полутона)
PITCH_BEND_MAX_VALUE = 8191.0         # Максимальное значение MIDI Pitch Bend

# ==============================================================================
# ДЕМО-МАССИВ ГЛИТЧ-ТОКЕНОВ (Сюда будут влетать данные из вашей LLM/скрипта)
# ==============================================================================
# Примеры реальных ID аномальных и глитч-токенов из больших языковых моделей
GLITCH_TOKENS = [
    9345, 23049, 1204, 88342, 4032, 99231, 1024, 456, 88342, 
    23049, 99231, 7763, 12, 4096, 65536, 100234, 432, 889
]

def calculate_19tet_pitch_bend(step_19_tet):
    """
    Математическое ядро: переводит абстрактный шаг 19-ТЕТ 
    в стандартную MIDI-ноту и точный сдвиг Pitch Bend.
    """
    # Вычисляем абсолютное смещение в центах от базовой ноты
    total_cents = step_19_tet * CENTS_PER_STEP_19TET
    
    # Находим ближайшую стандартную полутоновую ноту (12-ТЕТ)
    standard_note_offset = round(total_cents / 100.0)
    midi_note = BASE_NOTE + standard_note_offset
    
    # Считаем ошибку (остаток), которую нужно компенсировать колесом Pitch Bend
    error_cents = total_cents - (standard_note_offset * 100.0)
    
    # Переводим ошибку в шкалу MIDI Pitch Bend (-8192 до 8191)
    pitch_bend = int(round((error_cents / PITCH_BEND_RANGE_CENTS) * PITCH_BEND_MAX_VALUE))
    
    # Жесткий лимитер, чтобы не выйти за рамки MIDI-стандарта
    pitch_bend = max(-8192, min(8191, pitch_bend))
    
    return midi_note, pitch_bend

def run_glitch_generator(tokens, port, bpm=130):
    """
    Генератор паттерна. Превращает свойства токенов в музыкальную экспрессию.
    """
    # Вычисляем базовую длительность одного шага (16-я нота для сетки)
    step_time = 60.0 / bpm / 4.0 
    
    print(f" Скрипт запущен. Отправка 19-ТЕТ глитч-потока на TD-3 [{bpm} BPM]...")
    
    try:
        # Бесконечный цикл итерации по токенам для живого перформанса
        while True:
            for i, token in enumerate(tokens):
                # 1. ОПРЕДЕЛЕНИЕ ВЫСОТЫ ТОНА (19-ТЕТ)
                # Ограничиваем шаг размером двух октав в 19-ТЕТ (19 * 2 = 38 шагов)
                step_19_tet = token % 38 
                midi_note, pitch_bend_val = calculate_19tet_pitch_bend(step_19_tet)
                
                # 2. ОПРЕДЕЛЕНИЕ ДИНАМИКИ (ACCENT)
                # Если токен делится на 3 или его значение огромно — активируем акцент TD-3
                if token % 3 == 0 or token > 50000:
                    velocity = 127  # Зажжет лампу Accent на TD-3, фильтр "плюнет" звуком
                else:
                    velocity = random.randint(60, 85) # Обычная динамика
                
                # 3. АЛГОРИТМ СЛАЙДА (SLIDE / LEGATO)
                # Если следующий токен четный, мы НЕ выключаем текущую ноту сразу.
                # Они наложатся друг на друга, и аналоговая схема TD-3 включит скольжение (Slide)
                next_token = tokens[(i + 1) % len(tokens)]
                is_slide = (next_token % 2 == 0)
                
                # Исполнение команды: Сначала двигаем Pitch Bend, затем бьем ноту
                port.send(mido.Message('pitchwheel', pitch=pitch_bend_val))
                port.send(mido.Message('note_on', note=midi_note, velocity=velocity))
                
                if is_slide:
                    # Слайд: спим весь шаг, удерживая ноту включенной для следующего шага
                    time.sleep(step_time)
                else:
                    # Обычный шаг: держим ноту 70% времени шага, оставляя 30% на паузу (Staccato)
                    time.sleep(step_time * 0.7)
                    port.send(mido.Message('note_off', note=midi_note))
                    time.sleep(step_time * 0.3)
                    
    except KeyboardInterrupt:
        # Безопасный выход при нажатии Ctrl+C: тушим все ноты и сбрасываем Pitch Bend
        print("\n Генерация остановлена. Сброс MIDI-параметров.")
        port.send(mido.Message('pitchwheel', pitch=0))
        # Шлем команду "All Notes Off" на всякий случай
        port.send(mido.Message('control_change', control=123, value=0))

# ==============================================================================
# ТОЧКА ВХОДА
# ==============================================================================
if __name__ == '__main__':
    try:
        # Инициализация MIDI порта
        with mido.open_output(MIDI_PORT_NAME) as midi_out:
            # Запуск генератора. Экспериментируйте с BPM (например, 140 для плотного индастриала)
            run_glitch_generator(GLITCH_TOKENS, midi_out, bpm=135)
    except IOError:
        print(f"Ошибка: Не удалось найти или открыть MIDI-порт '{MIDI_PORT_NAME}'.")
        print("Доступные порты на вашем ПК:")
        print(mido.get_output_names())
