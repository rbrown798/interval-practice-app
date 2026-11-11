import random 
import pygame
import pygame.midi
import argparse
import numpy as np


# TODO: better input validation
#       toggle sound?
#
#       currently have: 
#             determine the 2nd note given the 1st note and interval
#
#       maybe have another mode:
#             determine the interval given two notes


NOTE_TO_OFFSET = {'C': 0, 
                  'D': 2, 
                  'E': 4, 
                  'F': 5, 
                  'G': 7, 
                  'A': 9, 
                  'B': 11}

OFFSET_TO_NOTE = {value: key for key, value in NOTE_TO_OFFSET.items()}

INTERVAL_NAMES = ['minor 2nd', 'major 2nd', 'minor 3rd', 'major 3rd', 
                  'perfect 4th', 'tritone', 'perfect 5th', 'minor 6th', 
                  'major 6th', 'minor 7th', 'major 7th']

ACCIDENTAL_KEY_OFFSETS = {pygame.K_UP: 1,
                          pygame.K_DOWN: -1,
                          pygame.K_RIGHT: 2,
                          pygame.K_LEFT: -2}

NOTE_DURATION_MS = 500


class IntervalGame:
    def __init__(self, reference_notes=[]):
        self._reference_notes = reference_notes
        self._has_midi = False
        self._running = False
        self._half_steps = 0
        self._offset1 = 0
        self._offset2 = 0
        self._interval_name = ''
        self._note1_name = ''

        self._question_text = ''
        self._note2_text = ''
        self._accidental_text = ''

        self._screen = None
        self._clock = None
        self._font = None
        self._keyboard_image = None
        self._sound = None
        self._midi_out = None

        self._keyboard_visible = False
        self._sound_on = True

    def _get_offset(self, note_name):
        if note_name.endswith('b'):
            offset = (NOTE_TO_OFFSET[note_name[0]] - 1) % 12

        elif note_name.endswith('#'):
            offset = (NOTE_TO_OFFSET[note_name[0]] + 1) % 12

        else:
            offset = NOTE_TO_OFFSET[note_name]

        return offset

    def _prepare(self):
        pygame.mixer.pre_init(frequency=44100, size=32, channels=1, 
                        allowedchanges=pygame.AUDIO_ALLOW_FREQUENCY_CHANGE)
        pygame.init()
        pygame.midi.init()

        output_id = pygame.midi.get_default_output_id()
        if output_id != -1:
            self._has_midi = True
            self._midi_out = pygame.midi.Output(output_id, latency=50)

        self._screen = pygame.display.set_mode((1280, 720))
        self._clock = pygame.time.Clock()
        self._font = pygame.font.Font(None, 64)
        self._keyboard_image = pygame.image.load('assets/PianoKeyboard.png')
        self._keyboard_image = self._keyboard_image.convert_alpha()

    def _exit(self):
        if self._has_midi:
            self._midi_out.close()

        pygame.midi.quit()
        pygame.mixer.quit()
        pygame.quit()

    def run(self):
        self._prepare()
        self._next_question()
        self._running = True

        while self._running:
            self._handle_events()
            self._update()
            self._draw()

        self._exit()

    def _handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self._running = False

            elif event.type == pygame.KEYDOWN:
                self._handle_keydown(event.key)

    def _handle_keydown(self, key):
        if key == pygame.K_q:
            self._running = False

        elif key == pygame.K_k:
            self._keyboard_visible = not self._keyboard_visible

        elif key in (pygame.K_EQUALS, pygame.K_PLUS):
            self._play_interval()

        elif key == pygame.K_MINUS:
            self._play_interval(descending=True)

        else:
            self._handle_note_key(key)

    def _handle_note_key(self, key):
        key_name = pygame.key.name(key).upper()

        if key_name in NOTE_TO_OFFSET:
            note_offset = NOTE_TO_OFFSET[key_name]

            pressed_keys = pygame.key.get_pressed()

            for key, accidental_offset in ACCIDENTAL_KEY_OFFSETS.items():
                if pressed_keys[key]:
                    note_offset = (note_offset + accidental_offset) % 12

            if note_offset == self._offset2: 
                self._next_question()

    def _update(self):
        self._question_text = f'What is a {self._interval_name} above {self._note1_name}?\n'
        self._note2_text = ''
        self._accidental_text = ''

        pressed_keys = pygame.key.get_pressed()

        for i in range(len(pressed_keys)):
            if pressed_keys[i]:
                key_name = pygame.key.name(i).upper()
                if key_name in NOTE_TO_OFFSET:
                    self._note2_text = key_name

        if pressed_keys[pygame.K_UP]:
            self._accidental_text = '#'
    
        elif pressed_keys[pygame.K_DOWN]:
            self._accidental_text = 'b'

        elif pressed_keys[pygame.K_RIGHT]:
            self._accidental_text = '##'

        elif pressed_keys[pygame.K_LEFT]:
            self._accidental_text = 'bb'

    def _draw(self):
        self._screen.fill('black')

        question_surface = self._font.render(self._question_text, True, 
                                       (255, 255, 255))

        accidental_surface = self._font.render(self._accidental_text, True, 
                                         (255, 255, 255))

        note_surface = self._font.render(self._note2_text, True, 
                                         (255, 255, 255))
    
        self._screen.blit(question_surface, (100, 100))
        self._screen.blit(note_surface, (100, 200))
        self._screen.blit(accidental_surface, (200, 200))

        if self._keyboard_visible:
            image_width = self._keyboard_image.get_width()
            left = (self._screen.get_width() - 3 * image_width) / 2

            for i in range(3):
                self._screen.blit(self._keyboard_image, 
                                  (left + i * image_width, 300))
    
        pygame.display.flip()
    
        self._clock.tick(60)  

    def _next_question(self):
        half_steps = self._half_steps
        offset1 = self._offset1
        note1_name = self._note1_name

        while (offset1 == self._offset1) and (half_steps == self._half_steps):
            half_steps = random.randint(1, 11)
        
            if self._reference_notes:
                note1_name = random.choice(self._reference_notes)
                offset1 = NOTE_TO_OFFSET[note1_name]

            else:
                offset1 = random.randint(0, 11)

        self._half_steps = half_steps
        self._offset1 = offset1
        
        self._offset2 = (offset1 + half_steps) % 12
        self._interval_name = INTERVAL_NAMES[half_steps - 1]

        if self._reference_notes:
            self._note1_name = note1_name

        else:
            self._note1_name = self._get_note_name(offset1)

        if self._sound_on:
            self._play_interval()

    def _get_note_name(self, offset):
        if offset in OFFSET_TO_NOTE:
            note_name = OFFSET_TO_NOTE[offset]
    
        else:
            if random.choice([True, False]):
                note_name = OFFSET_TO_NOTE[(offset - 1) % 12] + '#'
    
            else:
                note_name = OFFSET_TO_NOTE[(offset + 1) % 12] + 'b'

        return note_name

    def _play_interval(self, descending=False):
        note1 = 48 + self._offset1
        note2 = note1 + self._half_steps

        if descending:
            note1, note2 = note2, note1

        if self._has_midi:
            self._play_notes_midi(note1, note2)

        else:
            self._play_notes_sine(note1, note2)

    def _play_notes_midi(self, note1, note2):
        self._midi_out.write([
            [[0x90, note1, 127], pygame.midi.time()], 
            [[0x80, note1, 0], pygame.midi.time() + NOTE_DURATION_MS],
            [[0x90, note2, 127], pygame.midi.time() + NOTE_DURATION_MS],
            [[0x80, note2, 0], pygame.midi.time() + 2 * NOTE_DURATION_MS]
            ])

    def _play_notes_sine(self, note1, note2):
        sample_rate = pygame.mixer.get_init()[0]
        t = np.arange(sample_rate * NOTE_DURATION_MS * 0.001) / sample_rate

        freq1 = pygame.midi.midi_to_frequency(note1)
        freq2 = pygame.midi.midi_to_frequency(note2) 

        sine1 = 0.2 * np.sin(2 * np.pi * freq1 * t)        
        sine2 = 0.2 * np.sin(2 * np.pi * freq2 * t)

        buffer = np.concat((sine1, sine2)).astype(np.float32)
        
        if self._sound:
            self._sound.stop()

        self._sound = pygame.mixer.Sound(buffer)
        self._sound.play()


def is_note_valid(note_name):
    if note_name is None:
        return True

    if note_name in NOTE_TO_OFFSET:
        return True

    if (len(note_name) == 2) and (note_name.endswith('b') 
                                or note_name.endswith('#')
                                  ) and note_name[0] in NOTE_TO_OFFSET:
        return True

    return False


def are_notes_valid(note_names):
    for note in note_names:
        if is_note_valid(note) == False:
            return False

    return True


parser = argparse.ArgumentParser()
parser.add_argument('notes', nargs='*')
args = parser.parse_args()

if are_notes_valid(args.notes):
    game = IntervalGame(args.notes)
    game.run()

else:
    print('Invalid argument.')
