# Ultrasonic radar
This is a PyQt-based visualization for the ultrasonic radar.

# Install requirements
```
    # install qt and pyqt5
    # on mac:
    port install py35-pyqt5
    
    # install python dependencies
    pip install -r requirements.txt
```

# Run
```
    # run with mock data for testing
    python gui.py -f testdata.txt --mocked 
    
    # reading from a serial interface
    python gui.py -s /dev/cu.wchusbserial1410 --baud 9600 

    # reading from file
    python gui.py -f some_input_data.json 
```
