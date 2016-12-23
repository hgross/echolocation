#include <Servo.h>

#define sensor1TriggerPin 2
#define sensor1EchoPin 3
#define servoPwmPin 4
#define sensor2TriggerPin 5
#define sensor2EchoPin 6

/**
 * An abstraction for a ultrasonic measurement of a specific angle.
 */
struct Measurement {
  long distance; // distance in cm
  short angle; // angle in degrees (0,360)
};

/**
 * Encapsualtes a color definition in rgb
 */
struct Color {
  const short r; // (0,255)
  const short g; // (0,255)
  const short b; // (0,255)
};

/**
 * Consists of a threshold in cm and a color, that should be applied, if 
 * 
 */
struct RangeMapping {
  const int threshold; // the threshold
  const Color color; // the color to be used, if the distance is SMALLER than "threshold"
};

/**
 * Number of LEDs on the neopixel strip.
 */
const short NEOPIXEL_COUNT = 24;

/**
 * A list of mappings that maps thresholds (distances) to colors.
 * The list needs to be ordered (ascending by distance/threshold).
 * A lower distance wins over higher distances.
 */
const RangeMapping RANGE_MAPPINGS[] = {
  {20, {255, 0, 0}}, // red from 20cm or less
  {150, {255, 255, 0}}, // yellow from 150 
  {500, {0, 0, 255}}, // blue from 500
  {1000, {0, 255, 0}} // green from 1000  
};

/**
 * Degrees for each step by the servo.
 */
const float SERVO_STEP = 360.0/(float)NEOPIXEL_COUNT; // we have NEOPIXEL_COUNT LEDs on our neopixel ring, so we want to increase our angle by  => 360/24 = 15
/**
 * The delay between two servo/measurement steps.
 */
const int AFTER_MEASURE_DELAY = 150; // min 100
/**
 * Time needed by the motor to move to the desired position
 */
const int MOTOR_ACTION_TIME = 25;

/**
 * The servo that is moved between two measurements
 */
Servo servo;


void setup() {
  // configure output
  Serial.begin(9600);

  // configure leds
  pinMode(LED_BUILTIN, OUTPUT);

  // configure our ultrasonic sensors
  pinMode(sensor1TriggerPin, OUTPUT);
  pinMode(sensor1EchoPin, INPUT);
  pinMode(sensor2TriggerPin, OUTPUT);
  pinMode(sensor2EchoPin, INPUT);

  // configure servos
  servo.attach(servoPwmPin);  // attaches the servo on pin 9 to the servo object
}

/**
 * Measures the distance using one ultrasonic sensor.
 * Returns the distance in cm or -1, if reading failed.
 */
long measure(const int triggerPin, const int echoPin) {
  // TODO: a low-pass filter over multiple measurements would be nice to have here

  // ensure the echo pin is low
  if (digitalRead(echoPin) == HIGH) {
    // await the low state of the echo pin
    long e = pulseIn(echoPin, LOW);
  }

  // trigger pulse
  digitalWrite(triggerPin, LOW);
  delayMicroseconds(2);
  digitalWrite(triggerPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(triggerPin, LOW);
  
  // await echo
  const long duration = pulseIn(echoPin, HIGH);
  if (duration == 0) {
    // TODO: failed, for now we return -1
    return -1;
  }
  // calculate distance in cm
  const int distance = (duration / 2) / 29.1; // magic?
  return distance;
}

/**
 * Given a distance, determines the color to set by the static RangeMappings.
 */
Color determineColorByDistance(const long distance) {
  int colorIndex = 0;
  for(int i = 0; i < sizeof(RANGE_MAPPINGS) / sizeof(struct Color); i++) {
    if(RANGE_MAPPINGS[i].threshold <= distance) {
      colorIndex = i;
    } else {
      break;
    }
  }
  return RANGE_MAPPINGS[colorIndex].color;
}

/**
 * Mock for neoPixel api
 */
void setPixelColor(int pixelNo, int r, int g, int b) {
  //Serial.println("Setting neopixel " + String(pixelNo) + " to " + String(r) + "," + String(g) + "," + String(b));
}

/**
 * Sets the neopixel LEDs based on a discrete step we make.
 */
void setLEDs(int currentStep, Measurement* measurementBuffer) {
  // -- currentStep will be in [0, NEOPIXEL_COUNT/2]
  // we know that our servo steps map roughly to our led count
  // since we can only move 180° and we have two ultrasonic sensors head to head,
  // we also know, that for each 360/NEOPIXEL_COUNT wide step, our sensors point at the currentStep and the 180°
  // further angle as well (which is the (currentStep + (NUM_STEPS/2)-1)%NUM_STEPS-th step).
  int led1_no = currentStep;
  int led2_no = (currentStep + (NEOPIXEL_COUNT/2-1)) % NEOPIXEL_COUNT;
  int led1_distance = measurementBuffer[0].distance;
  int led2_distance = measurementBuffer[1].distance;

  // map distance to color
  Color led1_color = determineColorByDistance(led1_distance);
  Color led2_color = determineColorByDistance(led2_distance);
  
  // set neopixel leds
  // TODO: strip.setPixelColor(led1_no, led1_color.r, led1_color.g, led1_color.b);  
  // TODO: strip.setPixelColor(led2_no, led2_color.r, led2_color.g, led2_color.b);  
  setPixelColor(led1_no, led1_color.r, led1_color.g, led1_color.b);  
  setPixelColor(led2_no, led2_color.r, led2_color.g, led2_color.b);  

  // TODO: set brightness by scaling it from 100% to 20% with 100% = just set and 20% = not set for NEOPIXEL_COUNT/2-1 steps
}

/**
   Prints out the angle and distances as json data to the Serial interface.
*/
void communicateOutput(Measurement measurements[]) {
  const int distance0 = measurements[0].distance;
  const short angle0 = measurements[0].angle; // angle for sensor at 0 degree

  const int distance180 = measurements[1].distance;
  const int angle180 = measurements[1].angle; // angle for sensor at 180 degree
  const String json = "{\"measurements\": [{ \"angle\": " + String(angle0) + ", \"distance\": " + String(distance0) + " }, { \"angle\": " + String(angle180) + ", \"distance\": " + String(distance180) + " }]}";
  Serial.println(json);
}

/**
 * Measures the distance for both ultrasonic sensors and writes the results into the given meassurementBuffer
 */
void measureAll(short currentAngle, Measurement* measurementBuffer) {
  digitalWrite(LED_BUILTIN, HIGH); // signal measurement phase
  long distance0 = measure(sensor1TriggerPin, sensor1EchoPin);
  long distance180 = measure(sensor2TriggerPin, sensor2EchoPin); // TODO measure with two sensors
  //long distance180 = -1;
  digitalWrite(LED_BUILTIN, LOW);
  

  // write to buffer, if given
  if(measurementBuffer) {
    // build the result objects
    Measurement measurement0, measurement180;
    measurement0.angle = currentAngle; // angle for sensor at 0 degree
    measurement0.distance = distance0;
    measurement180.angle = 180 + currentAngle; // angle for sensor at 180 degree
    measurement180.distance = distance180;
  
    // add them to the output buffer
    measurementBuffer[0] = measurement0;
    measurementBuffer[1] = measurement180;
  }
}

void loop() {
  float currentAngle;
  Measurement measurementBuffer[2];
  int stepNo = 0;
  
  // move servo continuously forth and back by discrete angle
  for (currentAngle = 0; currentAngle <= 180; currentAngle += SERVO_STEP) { // goes from 0 degrees to 180 degrees
    servo.write(currentAngle);
    delay(MOTOR_ACTION_TIME);
    measureAll(currentAngle, measurementBuffer);
    setLEDs(stepNo, measurementBuffer);
    communicateOutput(measurementBuffer);
    delay(AFTER_MEASURE_DELAY);
    stepNo += 1;
  }

  stepNo = NEOPIXEL_COUNT/2-1;
  for (currentAngle = 180 - SERVO_STEP; currentAngle > 0; currentAngle -= SERVO_STEP) { // goes from 180 degrees to 0 degrees
    servo.write(currentAngle);
    delay(MOTOR_ACTION_TIME);
    measureAll(currentAngle, measurementBuffer);
    setLEDs(stepNo, measurementBuffer);
    communicateOutput(measurementBuffer);
    delay(AFTER_MEASURE_DELAY);
    stepNo -= 1;
  }
}
