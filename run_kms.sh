#!/bin/sh

# Use the Debian/Raspberry Pi build of Pygame and SDL, which includes KMS/DRM.
PYGAME_KMS_ROOT=${PYGAME_KMS_ROOT:-"$HOME/.local/pygame-kms"}
export PYTHONPATH="$PYGAME_KMS_ROOT/usr/lib/python3/dist-packages"
export LD_LIBRARY_PATH="$PYGAME_KMS_ROOT/usr/lib/aarch64-linux-gnu:$PYGAME_KMS_ROOT/usr/lib/aarch64-linux-gnu/pulseaudio${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
export LIBGL_DRIVERS_PATH="$PYGAME_KMS_ROOT/usr/lib/aarch64-linux-gnu/dri"
export GBM_BACKENDS_PATH="$PYGAME_KMS_ROOT/usr/lib/aarch64-linux-gnu/gbm"
export __EGL_VENDOR_LIBRARY_FILENAMES="$PYGAME_KMS_ROOT/usr/share/glvnd/egl_vendor.d/50_mesa.json"

# card1 owns the Raspberry Pi HDMI connectors; card0 is the V3D render device.
export SDL_VIDEODRIVER=kmsdrm
export SDL_KMSDRM_DEVICE_INDEX=1
export SDL_AUDIODRIVER=dummy

exec /usr/bin/python3 main.py
