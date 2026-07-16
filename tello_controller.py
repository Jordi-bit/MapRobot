import time
import threading
import cv2
import numpy as np
import os
from datetime import datetime

try:
    from djitellopy import Tello
    TELLO_AVAILABLE = True  # ✅ djitellopy importada correctamente
except ImportError:
    TELLO_AVAILABLE = False
    print("⚠️ djitellopy no instalada. Usando modo SIMULACIÓN.")

class TelloController:
    def __init__(self):
        self.drone = None
        self.connected = False
        self.stream_on = False
        self.thread = None
        self.force_simulation = False  # Si True, ignora el dron real aunque djitellopy esté disponible
        # Nueva lógica de cámara
        self.recording = False
        self.is_video_mode = True # True: Video, False: Foto
        self.video_writer = None
        self.frame_to_save = None
        
    def conectar(self):
        if not TELLO_AVAILABLE or self.force_simulation:
            modo = "forzada" if self.force_simulation else "sin djitellopy"
            print(f"🤖 [MOCK] Tello conectado (Modo Simulación — {modo})")
            self.connected = True
            return True
            
        try:
            self.drone = Tello()
            self.drone.connect()
            print(f"✅ Tello conectado. Batería: {self.drone.get_battery()}%")
            self.connected = True
            return True
        except Exception as e:
            print(f"❌ Error al conectar Tello: {e}")
            self.connected = False
            return False
            
    def iniciar_video(self):
        if not self.connected or self.stream_on: return
        
        if TELLO_AVAILABLE and self.drone is not None and not self.force_simulation:
            self.drone.streamon()
            self.stream_on = True
            # Esperar a que el stream esté listo antes de leer frames
            time.sleep(2)
            self.thread = threading.Thread(target=self._ver_video)
            self.thread.daemon = True
            self.thread.start()
        else:
            print("🤖 [MOCK] Iniciando streaming de video ficticio...")
            self.stream_on = True
            self.thread = threading.Thread(target=self._ver_video_mock)
            self.thread.daemon = True
            self.thread.start()

    def _ver_video(self):
        while self.stream_on:
            self.frame_to_save = self.drone.get_frame_read().frame
            
            # Si estamos grabando, guardar el frame
            if self.recording and self.video_writer:
                self.video_writer.write(self.frame_to_save)
            
            # Mostrar feedback visual de grabación
            mostrar_frame = self.frame_to_save.copy()
            if self.recording:
                cv2.circle(mostrar_frame, (30, 30), 10, (0, 0, 255), -1)
                cv2.putText(mostrar_frame, "REC", (50, 40), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

            cv2.imshow("Tello Camera Feed", mostrar_frame)
            if cv2.waitKey(1) & 0xFF == ord('c'):
                self.stream_on = False
                break
        
        if self.recording: self.stop_recording()
        cv2.destroyAllWindows()

    def _ver_video_mock(self):
        print("📷 Intentando abrir webcam (puede tardar unos segundos)...")
        import sys
        if sys.platform.startswith('win'):
            cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        else:
            cap = cv2.VideoCapture(0)
            
        if not cap.isOpened():
            print("⚠️ No se pudo abrir la webcam (índice 0). Generando ruido visual...")
            
        while self.stream_on:
            ret, frame = False, None
            if cap.isOpened():
                ret, frame = cap.read()
                
            if not ret:
                # Si no hay webcam, mostrar ruido
                frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
            
            self.frame_to_save = frame
            
            # Graba si es necesario
            if self.recording and self.video_writer:
                self.video_writer.write(self.frame_to_save)

            mostrar_frame = self.frame_to_save.copy()
            text_color = (0, 0, 255) if self.recording else (255, 255, 255)
            cv2.putText(mostrar_frame, "[MODO SIMULACION TELLO]", (50, 50), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1, text_color, 2)
            
            if self.recording:
                cv2.circle(mostrar_frame, (30, 30), 10, (0, 0, 255), -1)
                cv2.putText(mostrar_frame, "REC", (50, 40), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

            cv2.imshow("Tello Camera Feed (MOCK)", mostrar_frame)
            
            if cv2.waitKey(1) & 0xFF == ord('c'):
                self.stream_on = False
                break
                
        if cap.isOpened():
            cap.release()
        cv2.destroyAllWindows()
        print("📷 Ventana de Tello cerrada.")

    def detener_video(self):
        """Detiene la transmisión de video."""
        self.stream_on = False
        if TELLO_AVAILABLE and self.drone is not None:
            try:
                self.drone.streamoff()
            except Exception as e:
                print(f"⚠️ Error al apagar stream: {e}")
        print("📷 Desactivando cámara...")

    def desconectar(self):
        """Desconecta completamente el dron y limpia recursos."""
        self.detener_video()
        if TELLO_AVAILABLE and self.drone is not None and self.connected:
            try:
                self.drone.end()
                print("🔌 Tello desconectado correctamente.")
            except Exception as e:
                print(f"⚠️ Error al desconectar: {e}")
        self.connected = False
        self.drone = None

    def enviar_comando(self, comando, *args):
        if not self.connected: return
        
        msg = f"Tello: Ejecutando {comando} {args if args else ''}"
        print(msg)
        
        if not TELLO_AVAILABLE or self.force_simulation: return  # Modo simulación: solo log
        
        try:
            if hasattr(self.drone, comando):
                func = getattr(self.drone, comando)
                func(*args)
        except Exception as e:
            print(f"❌ Error en comando {comando}: {e}")

    def despegar(self): 
        self.enviar_comando("takeoff")
        self.estabilizar()
        
    def aterrizar(self): 
        self.estabilizar()
        self.enviar_comando("land")
    
    def mover(self, direccion, distancia=30):
        # Direcciones: 'forward', 'back', 'left', 'right', 'up', 'down'
        self.enviar_comando(f"move_{direccion}", distancia)
        self.estabilizar()

    def estabilizar(self):
        """Envía comandos de velocidad 0 para forzar al dron a mantenerse estable en el sitio."""
        if not self.connected: return
        if not TELLO_AVAILABLE or self.force_simulation: return
        
        try:
            if hasattr(self.drone, 'send_rc_control'):
                self.drone.send_rc_control(0, 0, 0, 0)
                print("Tello: Estabilizando en el sitio (RC 0,0,0,0)")
        except Exception as e:
            print(f"❌ Error al estabilizar Tello: {e}")

    # --- NUEVAS FUNCIONES DE CÁMARA ---
    
    def toggle_mode(self):
        self.is_video_mode = not self.is_video_mode
        print(f"📷 Modo de cámara cambiado a: {'VIDEO' if self.is_video_mode else 'FOTO'}")
        return self.is_video_mode

    def take_photo(self):
        if self.frame_to_save is not None:
            if not os.path.exists("capturas"): os.makedirs("capturas")
            filename = f"capturas/foto_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            cv2.imwrite(filename, self.frame_to_save)
            print(f"📸 Foto guardada: {filename}")
            return True
        print("⚠️ No hay imagen disponible para capturar.")
        return False

    def toggle_recording(self):
        if not self.recording:
            # Empezar a grabar
            if self.frame_to_save is not None:
                if not os.path.exists("capturas"): os.makedirs("capturas")
                height, width, _ = self.frame_to_save.shape
                filename = f"capturas/video_{datetime.now().strftime('%Y%m%d_%H%M%S')}.avi"
                fourcc = cv2.VideoWriter_fourcc(*'XVID')
                self.video_writer = cv2.VideoWriter(filename, fourcc, 20.0, (width, height))
                self.recording = True
                print(f"🎥 Grabando vídeo: {filename}")
                return True
        else:
            # Parar de grabar
            self.recording = False
            if self.video_writer:
                self.video_writer.release()
                self.video_writer = None
            print("🛑 Grabación finalizada.")
            return False
        return False

if __name__ == "__main__":
    tello = TelloController()
    if tello.conectar():
        tello.iniciar_video()
        print("Usa Ctrl+C para salir.")
        try:
            while True: time.sleep(1)
        except KeyboardInterrupt:
            tello.stream_on = False
            tello.aterrizar()
