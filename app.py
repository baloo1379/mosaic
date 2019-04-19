from PIL import Image
from flask import Flask, send_file, make_response, jsonify
from flask_restful import Resource, Api, reqparse, inputs
import re
import requests
import shutil
import collage
import random
import os

app = Flask(__name__)
api = Api(app)

debug_file = 'photo.jpg'


class mosaica(Resource):
    random = False
    resolution = {'x': 2048, 'y': 2048}
    photos_urls = []
    photos_number = 0
    photos_paths = []

    def get(self):
        self.random = False
        self.resolution = {'x': 2048, 'y': 2048}
        self.photos_urls = []
        self.photos_number = 0
        self.photos_paths = []

        parser = reqparse.RequestParser()
        parser.add_argument('losowo', type=int)
        parser.add_argument('rozdzielczosc', type=str)
        parser.add_argument('zdjecia', type=str, required=True)
        args = parser.parse_args(strict=True)

        self.random = args.losowo == 1

        if args.rozdzielczosc is not None:
            if re.search("\d+x\d+", args.rozdzielczosc) is not None:
                self.resolution['x'] = int(args.rozdzielczosc.split('x')[0])
                self.resolution['y'] = int(args.rozdzielczosc.split('x')[1])

        self.photos_urls = args.zdjecia.split(',')
        try:
            self.photos_urls.remove('')
            del self.photos_urls[self.photos_urls.index('')]
        except ValueError:
            pass

        try:
            for url in self.photos_urls:
                url = inputs.url(url)
        except ValueError as e:
            resp = make_response(jsonify({'message': {'zdjecia': str(e)}}), 400)
            return resp


        self.photos_number = len(self.photos_urls)

        if self.photos_number > 8 or self.photos_number < 1 or self.photos_urls[0] is '':
            resp = make_response(jsonify({'message': {'zdjecia': 'Check your URLs'}}), 400)
            return resp

        for i in range(self.photos_number):
            r = requests.get(self.photos_urls[i], stream=True)
            if r.status_code == 200 and (r.headers['content-type'] == 'image/jpg' or r.headers['content-type'] == 'image/png' or r.headers['content-type'] == 'image/jpeg'):
                path = str(i)+'.jpg'
                self.photos_paths.append(path)
                with open(path, 'wb') as f:
                    r.raw.decode_content = True
                    shutil.copyfileobj(r.raw, f)
            else:
                resp = make_response(jsonify({'message': {'zdjecia': {self.photos_urls[i]: 'Can\'t download from this host'}}}), 400)
                return resp

        if self.random:
            random.shuffle(self.photos_paths)

        if self.photos_number == 1:
            final_im = Image.open(self.photos_urls[0])
            final_im = final_im.resize((self.resolution['x'], self.resolution['y']))
            final_im.save('mozaika.jpg', "JPEG")
            final_im.close()
        else:
            result = collage.create_collage(self.photos_paths, self.resolution['x'], self.photos_number / 2)
            result.save('mozaika.jpg', "JPEG")

        final_im = Image.open('mozaika.jpg')
        final_im = final_im.resize((self.resolution['x'], self.resolution['y']))
        final_im.save('mozaika.jpg', "JPEG")
        final_im.close()

        for path in self.photos_paths:
            if os.path.exists(path):
                os.remove(path)

        return send_file('mozaika.jpg', mimetype='image/jpg')


api.add_resource(mosaica, '/mozaika')


if __name__ == '__main__':
    app.run(debug=True)
