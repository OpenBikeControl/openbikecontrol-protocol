# OpenBikeControl Protocol Specification

## Overview

OpenBikeControl is an open protocol for wireless input devices to control cycling trainer applications. It enables standardized communication between BLE controllers, apps, and the training app itself.

### Motivation

Many cycling trainer apps support various actions that traditionally require:
- On-screen button clicks
- Keyboard input
- Proprietary BLE controllers

OpenBikeControl provides a unified, open protocol that:
- **Easy to implement** - Simple data format with minimal overhead
- **Open standard** - No licensing fees or proprietary restrictions
- **Dual connectivity** - Supports both BLE and network-based connections
- **Already partially adopted** - Similar technology as the existing "Direct Connect" implementations
- **Apple-friendly** - Does not rely on manufacturer data fields that cannot be emulated on iOS

Continue along at [PROTOCOL.md](PROTOCOL.md).

## Trainer apps
These are the trainer apps that have, or plan to, implement support for the OpenBikeControl protocol, allowing users to control them using compatible BLE controllers or network-based input devices.

### MyWhoosh

![MyWhoosh logo](implementations/mywhoosh.png)

[https://mywhoosh.com/](https://mywhoosh.com/)

### Rouvy

![Rouvy logo](implementations/rouvy.svg)

[https://rouvy.com/](https://rouvy.com/)

### TrainingPeaks

![TrainingPeaks logo](implementations/trainingpeaks.png)

[https://www.trainingpeaks.com/](https://www.trainingpeaks.com/)

### icTrainer

![icTrainer logo](implementations/ictrainer.png)

[https://ictrainer.de/](https://ictrainer.de/)

# Implementations

### BikeControl
The OpenBikeControl protocol is already implemented into the BikeControl app, allowing the control of supported trainer apps, using a good amount of different input devices:

![BikeControl logo](implementations/bikecontrol.png)

[https://bikecontrol.app/](https://bikecontrol.app/)
