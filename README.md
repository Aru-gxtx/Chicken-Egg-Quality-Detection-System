# Chicken Egg Quality Detection System

(to be edited)

This a the repository for everything needed in the Chicken Egg Quality Detection Device Using Image Processing for Efficient Rural Production study by Aru-gxtx (Matthew Arni Bendo) and RafaelAntonioUy (Rafael Antonio E. Uy). Take note that this repository only tackles the software part of the study and not the hardware parts hence recreating this would require creating a hardware system parts. Although manually is possible but this area will be tackled later on.

First, for the model, you could use the already trained model by us via the train folder, weights, best.pt as its default. But if you want to recreate the model creation, you should:
1. provide your datasets images with annotation at the specified datasets folder, images and labels (for annotation) are divided into different figures. Make sure the annotated values are already separated into each classes (e.g. AA, A, B, Inedible (the default)).
2. use datasets_separator.py program to separate the datasets into 3 parts, train, val, and test. This is for better model output and to remove the risks of overfitting.
3. run the data.yaml program so that it will classify the annotated value for each class.

For the egg quality detection on the other hand, the ```grand_final_setup.py``` is the overall Chicken Egg Quality Detection Device Using Image Processing for Efficient Rural Production process. To run this, you would need:
1. control unit, in our case, we use Raspberry Pi 4 Model B but any is okay. The ```grand_final_setup.py``` should be seen here.
2. A Picamera, in our case, we use an IR Pi Camera but any is okay.
3. An ESP32 Connected via port USB0 to the Pi (correct port is necessary). The ```servo_controls.cpp``` should be seen here.
4. A monitor for the Pi.
The program is plug and playable so it runs if it recieves power. Note that it would not run if any of the above conditions aren't met. If you just want to replicate it and run it yourself, you first need to create a virtual environment like venv, then install of the requirements from the ```requirements.txt``` then run the python program. To make it plug and playable, I forgor, just search it yourself again teehee. ;>

To test each functions manually, you could use
