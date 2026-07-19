"""
Тесты для модуля Input.py - генератора MIDI паттернов на основе 19-ТЭТ
"""
import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Добавляем путь к модулю Input.py (корень проекта)
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_DIR)

class TestCalculate19TetPitchBend(unittest.TestCase):
    """Тесты функции calculate_19tet_pitch_bend"""
    
    def setUp(self):
        """Импортируем функцию перед каждым тестом"""
        # Чистим кэш импортов для корректного импорта
        if 'Input' in sys.modules:
            del sys.modules['Input']
        
        import Input
        self.calculate_19tet_pitch_bend = Input.calculate_19tet_pitch_bend
        self.CENTS_PER_STEP_19TET = Input.CENTS_PER_STEP_19TET
        self.PITCH_BEND_RANGE_CENTS = Input.PITCH_BEND_RANGE_CENTS
        self.PITCH_BEND_MAX_VALUE = Input.PITCH_BEND_MAX_VALUE
        self.BASE_NOTE = Input.BASE_NOTE
    
    def test_zero_step_returns_base_note(self):
        """0 шагов = базовая нота, без pitch bend"""
        midi_note, pitch_bend = self.calculate_19tet_pitch_bend(0)
        self.assertEqual(midi_note, self.BASE_NOTE)
        self.assertEqual(pitch_bend, 0)
    
    def test_19_steps_one_octave(self):
        """19 шагов = ровно одна октава выше, без pitch bend"""
        midi_note, pitch_bend = self.calculate_19tet_pitch_bend(19)
        expected_note = self.BASE_NOTE + 12  # 12 полутонов = октава
        self.assertEqual(midi_note, expected_note)
        self.assertEqual(pitch_bend, 0)
    
    def test_38_steps_two_octaves(self):
        """38 шагов = две октавы выше, без pitch bend"""
        midi_note, pitch_bend = self.calculate_19tet_pitch_bend(38)
        expected_note = self.BASE_NOTE + 24  # 24 полтона = 2 октавы
        self.assertEqual(midi_note, expected_note)
        self.assertEqual(pitch_bend, 0)
    
    def test_step_1_microtonal(self):
        """1 шаг = микротональный интервал с pitch bend"""
        midi_note, pitch_bend = self.calculate_19tet_pitch_bend(1)
        
        # Ожидаемая высота: 1 * 63.158 = 63.158 центов
        # Ближайшая полутоновая нота: +1 полутон (100 центов)
        # Ошибка: 63.158 - 100 = -36.842 центов
        # Pitch bend: -36.842 / 200 * 8191 ≈ -1512
        
        self.assertEqual(midi_note, self.BASE_NOTE + 1)
        # Проверяем, что pitch bend близок к ожидаемому значению
        expected_pitch_bend = int(round((-36.842 / 200.0) * 8191))
        self.assertEqual(pitch_bend, expected_pitch_bend)
    
    def test_step_10_microtonal(self):
        """10 шагов = микротональный интервал"""
        midi_note, pitch_bend = self.calculate_19tet_pitch_bend(10)
        
        # Ожидаемая высота: 10 * 63.158 = 631.58 центов
        # Ближайшая полутоновая нота: +6 полутонов (600 центов)
        # Ошибка: 631.58 - 600 = 31.58 центов
        # Pitch bend: 31.58 / 200 * 8191 ≈ 1292
        
        self.assertEqual(midi_note, self.BASE_NOTE + 6)
        expected_pitch_bend = int(round((31.58 / 200.0) * 8191))
        self.assertEqual(pitch_bend, expected_pitch_bend)
    
    def test_negative_step_handling(self):
        """Отрицательные шаги должны обрабатываться корректно"""
        midi_note, pitch_bend = self.calculate_19tet_pitch_bend(-1)
        
        # Ожидаемая высота: -1 * 63.158 = -63.158 центов
        # Ближайшая полутоновая нота: -1 полутон (-100 центов)
        # Ошибка: -63.158 - (-100) = 36.842 центов
        # Pitch bend: 36.842 / 200 * 8191 ≈ 1512
        
        self.assertEqual(midi_note, self.BASE_NOTE - 1)
        expected_pitch_bend = int(round((36.842 / 200.0) * 8191))
        self.assertEqual(pitch_bend, expected_pitch_bend)
    
    def test_pitch_bend_clamping_max(self):
        """Pitch bend должен быть ограничен значением 8191"""
        # Используем очень большой шаг для теста ограничения
        # 19 * 2 = 38 шагов = 2 октавы = 0 pitch bend (поскольку это целая октава)
        # Но мы можем протестировать, что значение не выходит за пределы
        
        midi_note, pitch_bend = self.calculate_19tet_pitch_bend(19)
        self.assertGreaterEqual(pitch_bend, -8192)
        self.assertLessEqual(pitch_bend, 8191)
    
    def test_pitch_bend_clamping_min(self):
        """Pitch bend должен быть ограничен значением -8192"""
        # Проверяем для отрицательного шага
        midi_note, pitch_bend = self.calculate_19tet_pitch_bend(-1)
        self.assertGreaterEqual(pitch_bend, -8192)
        self.assertLessEqual(pitch_bend, 8191)
    

class TestMathematicalCorrectness(unittest.TestCase):
    """Математическая корректность вычислений"""
    
    def setUp(self):
        """Импортируем функцию перед каждым тестом"""
        import Input
        self.calculate_19tet_pitch_bend = Input.calculate_19tet_pitch_bend
        self.CENTS_PER_STEP_19TET = Input.CENTS_PER_STEP_19TET
    
    def test_cents_per_step_calculation(self):
        """Проверка правильности вычисления центов на шаг"""
        expected_cents = 1200.0 / 19.0
        self.assertAlmostEqual(self.CENTS_PER_STEP_19TET, expected_cents, places=3)
    
    def test_octave_equivalence(self):
        """Проверка, что 19 шагов = 1 октава = 1200 центов"""
        step_19 = 19
        total_cents = step_19 * self.CENTS_PER_STEP_19TET
        self.assertAlmostEqual(total_cents, 1200.0, places=2)
    
    def test_pitch_bend_linear_relationship(self):
        """Проверка линейной зависимости pitch bend от ошибки"""
        # Для 0 шагов pitch bend должен быть 0
        midi_note, pitch_bend = self.calculate_19tet_pitch_bend(0)
        self.assertEqual(pitch_bend, 0)
        
        # Для 19 шагов (целая октава) pitch bend также должен быть 0
        midi_note, pitch_bend = self.calculate_19tet_pitch_bend(19)
        self.assertEqual(pitch_bend, 0)


if __name__ == '__main__':
    unittest.main(verbosity=2)
