import pygame
import sys
import ctypes
# ヘッドレス環境で Pygame 単体の動作を確認する間は無効化
# import cv2
from mock_gps import MockGPS
# from boot_animation import BootAnimation
# from rear_camera import Rear_Camera


CAMERA_SIZE = (240, 180)
CAMERA_MARGIN = 20

TEXT_X = 20
VALUE_X = 200
TEXT_Y = 20
TEXT_LINE_HEIGHT = 40

# color
BLACK = (0, 0, 0)
GREEN = (0, 255, 0)
RED = (255, 0, 0)

clock = pygame.time.Clock()


class GLFramePresenter:
    """Upload a Pygame Surface and present it as a full-screen GLES texture."""

    GL_COLOR_BUFFER_BIT = 0x00004000
    GL_FLOAT = 0x1406
    GL_FRAGMENT_SHADER = 0x8B30
    GL_LINEAR = 0x2601
    GL_RGBA = 0x1908
    GL_TEXTURE_2D = 0x0DE1
    GL_TEXTURE_MAG_FILTER = 0x2800
    GL_TEXTURE_MIN_FILTER = 0x2801
    GL_TRIANGLE_STRIP = 0x0005
    GL_UNSIGNED_BYTE = 0x1401
    GL_VERTEX_SHADER = 0x8B31

    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.gl = ctypes.CDLL("libGLESv2.so.2")
        self._configure_functions()
        self.program = self._create_program()
        self.texture = ctypes.c_uint()
        self.gl.glGenTextures(1, ctypes.byref(self.texture))
        self.gl.glBindTexture(self.GL_TEXTURE_2D, self.texture.value)
        self.gl.glTexParameteri(self.GL_TEXTURE_2D, self.GL_TEXTURE_MIN_FILTER, self.GL_LINEAR)
        self.gl.glTexParameteri(self.GL_TEXTURE_2D, self.GL_TEXTURE_MAG_FILTER, self.GL_LINEAR)
        self.gl.glTexImage2D(
            self.GL_TEXTURE_2D, 0, self.GL_RGBA, width, height, 0,
            self.GL_RGBA, self.GL_UNSIGNED_BYTE, None,
        )
        self.gl.glViewport(0, 0, width, height)

    def _configure_functions(self):
        self.gl.glCreateShader.restype = ctypes.c_uint
        self.gl.glCreateProgram.restype = ctypes.c_uint
        self.gl.glGetAttribLocation.restype = ctypes.c_int
        self.gl.glGetUniformLocation.restype = ctypes.c_int
        self.gl.glClearColor.argtypes = [
            ctypes.c_float,
            ctypes.c_float,
            ctypes.c_float,
            ctypes.c_float,
        ]
        self.gl.glGetAttribLocation.argtypes = [ctypes.c_uint, ctypes.c_char_p]
        self.gl.glShaderSource.argtypes = [
            ctypes.c_uint, ctypes.c_int,
            ctypes.POINTER(ctypes.c_char_p), ctypes.POINTER(ctypes.c_int),
        ]
        self.gl.glVertexAttribPointer.argtypes = [
            ctypes.c_uint, ctypes.c_int, ctypes.c_uint, ctypes.c_ubyte,
            ctypes.c_int, ctypes.c_void_p,
        ]
        texture_args = [
            ctypes.c_uint, ctypes.c_int, ctypes.c_int, ctypes.c_int,
            ctypes.c_int, ctypes.c_int, ctypes.c_uint, ctypes.c_uint,
            ctypes.c_void_p,
        ]
        self.gl.glTexImage2D.argtypes = texture_args
        self.gl.glTexSubImage2D.argtypes = texture_args

    def _compile_shader(self, shader_type, source):
        shader = self.gl.glCreateShader(shader_type)
        source_bytes = source.encode("ascii")
        source_pointer = ctypes.c_char_p(source_bytes)
        self.gl.glShaderSource(shader, 1, ctypes.byref(source_pointer), None)
        self.gl.glCompileShader(shader)
        return shader

    def _create_program(self):
        vertex_shader = self._compile_shader(
            self.GL_VERTEX_SHADER,
            "attribute vec2 position; attribute vec2 texcoord; varying vec2 uv; "
            "void main(){ gl_Position=vec4(position,0.0,1.0); uv=texcoord; }",
        )
        fragment_shader = self._compile_shader(
            self.GL_FRAGMENT_SHADER,
            "precision mediump float; varying vec2 uv; uniform sampler2D image; "
            "void main(){ gl_FragColor=texture2D(image,uv); }",
        )
        program = self.gl.glCreateProgram()
        self.gl.glAttachShader(program, vertex_shader)
        self.gl.glAttachShader(program, fragment_shader)
        self.gl.glLinkProgram(program)
        return program

    def present(self, surface):
        pixels = pygame.image.tostring(surface, "RGBA", False)
        pixel_buffer = ctypes.create_string_buffer(pixels)
        self.gl.glBindTexture(self.GL_TEXTURE_2D, self.texture.value)
        self.gl.glTexSubImage2D(
            self.GL_TEXTURE_2D, 0, 0, 0, self.width, self.height,
            self.GL_RGBA, self.GL_UNSIGNED_BYTE, ctypes.cast(pixel_buffer, ctypes.c_void_p),
        )
        self.gl.glUseProgram(self.program)
        vertices = (ctypes.c_float * 16)(
            -1, -1, 0, 1, 1, -1, 1, 1,
            -1, 1, 0, 0, 1, 1, 1, 0,
        )
        position = self.gl.glGetAttribLocation(self.program, b"position")
        texcoord = self.gl.glGetAttribLocation(self.program, b"texcoord")
        stride = 4 * ctypes.sizeof(ctypes.c_float)
        self.gl.glEnableVertexAttribArray(position)
        self.gl.glEnableVertexAttribArray(texcoord)
        self.gl.glVertexAttribPointer(
            position, 2, self.GL_FLOAT, False, stride,
            ctypes.cast(vertices, ctypes.c_void_p),
        )
        self.gl.glVertexAttribPointer(
            texcoord, 2, self.GL_FLOAT, False, stride,
            ctypes.cast(ctypes.byref(vertices, 2 * ctypes.sizeof(ctypes.c_float)), ctypes.c_void_p),
        )
        self.gl.glClearColor(0.0, 0.0, 0.0, 1.0)
        self.gl.glClear(self.GL_COLOR_BUFFER_BIT)
        self.gl.glDrawArrays(self.GL_TRIANGLE_STRIP, 0, 4)
        pygame.display.flip()


# rear_camera = Rear_Camera()
# boot_animation = BootAnimation()

def draw_metric(screen, font, row, label, value):
    y = TEXT_Y + (TEXT_LINE_HEIGHT * row)
    label_text = font.render(label, True, GREEN)
    value_text = font.render(value, True, GREEN)
    screen.blit(label_text, [TEXT_X, y])
    screen.blit(value_text, [VALUE_X, y])


def format_elapsed_time(elapsed_seconds):
    total_seconds = int(elapsed_seconds)
    minutes = total_seconds // 60
    seconds = total_seconds % 60
    return f"{minutes:02d}:{seconds:02d}"


def main():
    '''
    ゲームの設定：
        画面の大きさ、タイトル、必要なファイルの用意など
    '''
    pygame.init()  # Pygameの初期化
    # frame_count = 0
    # KMSDRMのEGL/OpenGL ES描画面をPygameで作成する。
    screen = pygame.display.set_mode(
        (0, 0),
        pygame.FULLSCREEN | pygame.OPENGL | pygame.DOUBLEBUF,
    )
    screen_width, screen_height = pygame.display.get_window_size()
    frame = pygame.Surface((screen_width, screen_height))
    presenter = GLFramePresenter(screen_width, screen_height)
    pygame.mouse.set_visible(False)
    print(f"display driver: {pygame.display.get_driver()}")
    print(f"window size: {(screen_width, screen_height)}")
    font1 = pygame.font.Font(None, 30)
    font1_bold = pygame.font.Font(None, 30)
    gps = MockGPS()
    # surfarray = pygame.surfarray
    # boot_animation.play_boot_video(screen, pygame.time.Clock(), surfarray)


    '''
    ゲーム内の動き
    '''
    while True:
        # if frame_count <= 30:
        #     frame_count += 1

        gps_data = gps.read()
        frame.fill(BLACK)
        draw_metric(frame, font1, 0, "GPS", "FIX" if gps_data["fix"] else "SEARCHING")
        draw_metric(frame, font1, 1, "TIME", format_elapsed_time(gps_data["timestamp"]))
        draw_metric(frame, font1, 2, "SPEED", f"{gps_data['speed_kmh']:.1f}km/h")
        draw_metric(frame, font1, 3, "LATITUDE", f"{abs(gps_data['lat']):.6f}deg {gps_data['lat_dir']}")
        draw_metric(frame, font1, 4, "LONGITUDE", f"{abs(gps_data['lon']):.6f}deg {gps_data['lon_dir']}")
        draw_metric(frame, font1, 5, "ALTITUDE", f"{gps_data['altitude_m']:.1f}m")
        draw_metric(frame, font1, 6, "HEADING", f"{gps_data['heading_deg']:.0f}deg")
        draw_metric(frame, font1, 7, "SATELLITES", str(gps_data["satellites"]))

        camera_rect = pygame.Rect(
            screen_width - CAMERA_SIZE[0] - CAMERA_MARGIN,
            screen_height - CAMERA_SIZE[1] - CAMERA_MARGIN,
            CAMERA_SIZE[0],
            CAMERA_SIZE[1],
        )
        pygame.draw.rect(frame, RED, camera_rect, width=3, border_radius=18)
        camera_text = font1_bold.render("CAMERA NOT CONNECTED", True, RED)
        frame.blit(camera_text, camera_text.get_rect(center=camera_rect.center))
        # rear_camera.rear_camera(surfarray, screen, frame_count)
        presenter.present(frame)
        clock.tick(60)

        # イベント処理
        for event in pygame.event.get():
            if event.type == pygame.QUIT:  # 閉じるボタンが押されたら終了
                # rear_camera.camera.release()
                pygame.quit()
                sys.exit()
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    # rear_camera.camera.release()
                    pygame.quit()
                    sys.exit()
                    
if __name__ == '__main__':
    main()
