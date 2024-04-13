Hey this is a script that helps streamline the process of uploading to mixcloud.

In order to use it you may need to install some dependencies with pip install requests.

Also you will need to set up quick action in Automater, that runs the following shell script. 

~/path/to/python3 ~/path/to/uploader.py "$@"

Another thing you will need to do is create an application to setup api access in mixcloud at https://www.mixcloud.com/developers/#authorization and add the client id and secret to your script.

Once you've done that you can upload an mp3 to mixcloud via a right-click.

make a json file with the same name to add the description tags and title.

Also add an image file with the same name to in the same folder which will be uploaded too.

I want to add file validation and add input to create the metadata if the json file isn't there.
