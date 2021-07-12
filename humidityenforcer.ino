#include "Arduino.h"

// analog pins for reading analog sensors
int soil_moisture_sensor = A0;
int water_tank_sensor = A1;

// these two pins are used to power the sensors
int soil_moisture_sensor_vcc = 7;
int water_tank_sensor_vcc = 6;

int water_overflow_sensor = 12; // 100K pull down resistor -> GND

void setup()
{	
	
	pinMode(soil_moisture_sensor_vcc, OUTPUT);
	pinMode(water_tank_sensor_vcc, OUTPUT);

	pinMode(water_overflow_sensor, INPUT);
	pinMode(soil_moisture_sensor, INPUT);
	pinMode(water_tank_sensor, INPUT);

	delay(1000);
	Serial.begin(9600);
}

void loop()
{


	// power the sensors
	digitalWrite(soil_moisture_sensor_vcc, HIGH);
	digitalWrite(water_tank_sensor_vcc, HIGH);
	delay(100);

	int soil_moisture_level = analogRead(soil_moisture_sensor);
	int water_tank_level = analogRead(water_tank_sensor);
	int water_overflow = digitalRead(water_overflow_sensor); // if there is water, it will short and this pin will read HIGH

	// power off the sensors
	digitalWrite(soil_moisture_sensor_vcc, LOW);
	digitalWrite(water_tank_sensor_vcc, LOW);


	// print one line, that contains 3 space delimited values
	// soil_moisture water_tank_level overflow
	Serial.print(soil_moisture_level);
	Serial.print(" ");
	Serial.print(water_tank_level);
	Serial.print(" ");
	Serial.print(water_overflow);
	Serial.println();

	delay(30000); // 30 sec sleep


}
