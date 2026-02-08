# Tab-It
Tab-it is a web app that allows users to upload songs, and get easy-to-read tab for the guitar part of the song. Built upon libraries and models developed by Meta Research and Spotify's Audio Intelligence Lab, the pipeline we developed picks out the guitar from multi-track songs, processed the audio waveforms into musical notes, intelligently places them on the guitar neck, and displays the result as easy-to-read tab.

# Inspiration
What inspired us to create Tab-it is our mutual interest in playing guitar. We realized that learning songs by ear is incredibly difficult for beginners, and finding accurate tabs for niche or new songs is often impossible. We wanted to build a tool that could listen to any song and give us a starting point to learn it immediately.

# How it is built
The Backend: We used Python for the heavy lifting. We utilized Meta's audio-separator library (powered by the Demucs model) to perform high-quality stem separation, which is then converted to MIDI by Basic Pitch from Spotify's Audio Intelligence Lab, then using the computer-aided musicology library music21 we transform this into well-organized musical notes, which are then run through a custom fretting algorithm to place the notes on the guitar neck. This pipeline was connected via Flask endpoints (one for audio-seperation, which runs on a Vultr compute node, and one for the rest of the pipeline and file uploading from the frontend).

The Frontend: Built with React and TypeScript. We used a component-based architecture to handle the file upload and tab display. Frontend receives a JSON object from the backend containing every note in the song, our React script maps those into a 6-string grid, and renders it as a clean text block. This let's the user visually see what string and fret to play.

# What's next for Tab-it
Tab-it works. We developed a complete, modular pipeline this weekend that takes in songs and provides guitar tab you can read and play along to. Seeing as this project is of personal interest to us both, we intend to continue working on it. While the pipeline outputs readable tabs, along the way notes can be dropped, added or shifted. With some model tweaking, fine-tuning, and potentially employing custom algorithms, we think this could be mitigated--allowing for very easy playing.

There are many factors to consider when placing notes onto the fretboard efficiently, and identifying chord patterns, hand shapes, and positions are all key to producing helpful tab. This is a very large area to be explored, and is a pretty pivotal part of our product, so more research and development will be put into this.

We intend to add database storage to allow the storage and retrieval of tabs, so users can build a library, and share their tabs with others. Other integrations could also be added, such as allowing users to record their own playing for feedback, or to get the tabs for their improvisations and solos. While we experimented with Vultr's cloud computing this weekend, re-examining the scalability, cost, and hosting of the product is definitely coming soon.

We are very excited to be bringing this product into reality, as we see great value for it in our own journey's as guitarists, and we know others will as well.

# Dependencies 

## Rebuild Dependencies for /backend
`pip install music21` \
`pip install basic-pitch`\
`pip install flask flask-cors` \
`pip install dotenv'

## For /auto-seperator
`pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu` (or equivelant torch installation) \
`winget install Gyan.FFmpeg` (ffmpeg dependency, requires terminal restart) \
`pip install audio-separator` \
`pip install flask`

## For /frontend/tab-it-frontend
`npm i`
