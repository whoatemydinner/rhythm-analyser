if __name__ == "__main__":
    pass


class AudioFile:
    def __init__(self, filepath):
        self.filepath, self.audio_data, self.format, self.sample_rate, self.title, self.artist = \
            None, None, None, None, None, None
        self._load_file(filepath)

    def _load_file(self, filepath):
        try:
            self.filepath = filepath
            self.audio_data, self.sample_rate = librosa.load(filepath, None, True, offset=0.0)
            self._read_tags(filepath)
        except Exception as e:
            print(e)
            raise ValueError("File {} is not a valid audio file".format(filepath))

    def _read_tags(self, filepath):
        tags = tt.TinyTag.get(filepath)
        self.artist = tags.artist
        self.title = tags.title

    def trim(self, start_time, end_time):
        start_sample = int(start_time * self.sample_rate)
        end_sample = int(end_time * self.sample_rate)

        self.audio_data = self.audio_data[start_sample:end_sample]
