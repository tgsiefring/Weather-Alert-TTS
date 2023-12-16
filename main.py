import requests
import time
import subprocess
from pyht.client import TTSOptions
from pyht import Client

# The intended usage of this program (as a personal project for myself) is to run headless on a raspberry pi and alert me with text to speech 
# of any weather concerns every 15 minutes.

#unfortunately openweather api tends to sometimes be wildly inaccurate, currently testing other apis. 

def get_weather_forecast(api_key):
    #openweather api to retrieve hourly chance of rain, temperature, wind speed, and weather alerts
    base_url = "https://api.openweathermap.org/data/2.5/onecall"
    #placeholder lat and long
    params = {"lat": 1, "lon": 1, "exclude": "current,minutely,daily", "appid": api_key}
    response = requests.get(base_url, params=params)
    data = response.json()

    hourly_forecast = data.get("hourly", [])
    alert_status = data.get("alerts", [])

    return hourly_forecast, alert_status

def kelvin_to_fahrenheit(kelvin):
    fahrenheit = (kelvin - 273.15) * 9/5 + 32
    return fahrenheit

# playht api used for text to speech.
playht_user_id = "id"  
playht_api_key = "key"  
output_file = "output.mp3"

client = Client(user_id=playht_user_id, api_key=playht_api_key)

def is_significant_change(last_temperature, current_temperature, threshold=10):
    return abs(current_temperature - last_temperature) >= threshold

def play_audio(audio_file):

    ffplay_path = "path"
    ffplay_command = r'{} -nodisp -autoexit "{}"'.format(ffplay_path, audio_file)
    subprocess.Popen(ffplay_command, shell=True).wait()

def main():
    #openweather api key
    api_key = "key"

    while True:
        
        hourly_forecast, alert_status = get_weather_forecast(api_key)

        if hourly_forecast:

            #hourly_forecast_info = hourly_forecast[0]

            # Extract the chance of rain from the first hourly entry.
            chance_of_precipitation = hourly_forecast[0].get("pop", 0)
            percentage_chance_of_precipitation = int(chance_of_precipitation * 100)

            # Extract the temperature.
            last_notified_temperature = None
            temperature = hourly_forecast[0].get("temp", 0)
            converted_temperature = kelvin_to_fahrenheit(temperature)
            temperature_trim = round(converted_temperature)

            # Extract the wind speed.
            wind_speed = hourly_forecast[0].get("wind_speed", 0)
            wind_speed_trim = round(wind_speed)

        # For testing purposes: this will show the relevant weather information even if it is not in the accepted ranges for the text to speech alerts
        print(f"the chance of precipitation test is {percentage_chance_of_precipitation}. the temperature test is {temperature_trim}. the wind speed test is {wind_speed_trim}.")
        time.sleep(2)

        # The chance of precipitation is read out if it is greater than or equal to 15 percent.
        if chance_of_precipitation >= 15:
            # Use Play.ht API to generate audio.
            options = TTSOptions(voice="s3://voice-cloning-zero-shot/d9ff78ba-d016-47f6-b0ef-dd630f59414e/female-cs/manifest.json")
            text_to_speech_precipitation = client.tts(f"The chance of precipitation is {percentage_chance_of_precipitation} percent in the next hour!", options)

            # Save the audio to a file.
            with open(output_file, "wb") as f:
                for chunk in text_to_speech_precipitation:
                    f.write(chunk)

            # Play the generated audio.
            play_audio(output_file)

            time.sleep(2)

        last_temperature_timestamp = time.time()

        # Temperature is read out if it is below 33 degrees or above 79 degrees. the program loops back through entirely every 15 minutes,
        # However the temperature is only read out if there has been a 10 degree difference since it was last read out or it has been one hour since it was last read out.
        # Reading out the temperature every 15 minutes when it stays hot or cold seemed a bit excessive.
        if (last_notified_temperature is None or abs(converted_temperature - last_notified_temperature) >= 10 
        or (time.time() - last_temperature_timestamp) >= 3600) and (converted_temperature < 33 or converted_temperature > 79):

            options = TTSOptions(voice="s3://voice-cloning-zero-shot/d9ff78ba-d016-47f6-b0ef-dd630f59414e/female-cs/manifest.json")
            text_to_speech_temperature = client.tts(f"please be advised the current temperature is {temperature_trim} degrees, I suggest you dress appropriately", options)

            # Save the audio to a file.
            with open(output_file, "wb") as h:
                for chunk in text_to_speech_temperature:
                    h.write(chunk)

            # Play the generated audio.
            play_audio(output_file)

            last_notified_temperature = converted_temperature
            last_temperature_timestamp = time.time()

            time.sleep(2)

        wind_speed_trim = round(wind_speed)

        # The wind speed is read out if it is greater than or equal to 15 miles per hour.
        if wind_speed_trim >= 15:
            options = TTSOptions(voice="s3://voice-cloning-zero-shot/d9ff78ba-d016-47f6-b0ef-dd630f59414e/female-cs/manifest.json")
            text_to_speech_wind = client.tts(f"warning, currently the wind speed is {wind_speed_trim} miles per hour", options)

            # Save the audio to a file.
            with open(output_file, "wb") as j:
                for chunk in text_to_speech_wind:
                    j.write(chunk)

            # Play the generated audio.
            play_audio(output_file)

            time.sleep(2)

        if alert_status:

            current_alert = alert_status[0].get("description", None)

            print(current_alert)

            options = TTSOptions(voice="s3://voice-cloning-zero-shot/d9ff78ba-d016-47f6-b0ef-dd630f59414e/female-cs/manifest.json")
            text_to_speech_alert1 = client.tts(current_alert, options)

            # Save the audio to a file.
            with open(output_file, "wb") as g:
                for chunk in text_to_speech_alert1:
                    g.write(chunk)

            # Play the generated audio.
            play_audio(output_file)

        time.sleep(900)

if __name__ == "__main__":
    main()
