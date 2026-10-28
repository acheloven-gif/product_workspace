# Разметка приложений по вертикалям для листа «Вертикали» (28.10).
# EXCLUDE — не приложения: маркетплейсы курсов, онлайн-школы, статьи-адвертореалы, товары, прочие сайты.
EXCLUDE = {
    'Coursera', 'Udemy', 'Preply', 'Kodland', 'Allright', 'Brighterly', 'Mate Academy',
    'HealthBoost (адвертореалы)', 'Health Insider', 'Healthtime', 'Health Horizon', 'ParentGuide', 'TopTravel',
    'Health Post', 'Fashion Radar', 'The Health Pulse', 'Newsi',
    'Memowrite', 'Old Ways Remedies', 'Ryoko', 'TinySnap', 'Zeely Health (zee.am)', 'Callyourdate', 'Jiji',
}
V = {
    'Фитнес и похудение': [
        'MadMuscles', 'Simple', 'Voy', 'Muscle Booster', 'FitMe', 'Lasta', 'Yoga-Go', 'BetterMe iFasting / iKeto (best.me)',
        'Metaboosting', 'OrganicFit', 'Reverse Health', 'Soonbody', 'Fit4me', 'Formula.care', 'Noom', 'KetoGo', 'MuscleCharge',
        'Harnafit', 'Muscle Monster', 'Slimkit', 'Ornament', 'MyBody (Cardi, MyDiabetes, PCOS)', 'Certified Fasting', 'TrimRx',
        'DanceFitme', 'greatapps:everdance', 'Dancebit', 'Her Bodhi', 'LifeMD', 'Ruut', 'VictoryScale', 'Skyfluence', 'Ultiself',
        'WalkingFL', 'NutriWalk', 'PerfectBody', 'Daily Yoga', 'Carnimeal', 'Fascia Program', 'JustStretch', 'FitPro (melab)',
        'greatapps:organic-fit', 'MyDiabetes',
    ],
    'Здоровье, гипноз, нервы': [
        'Hypnozio', 'Kure', 'The Coach', 'Leaply', 'Neurotoned', 'Superpower', 'greatapps:quiver', 'greatapps:senses',
        'InnerFlo', 'Longetic', 'Apollo', 'greatapps:welltory', 'MagnetMind', 'Deeply',
    ],
    'Утилиты: безопасность, поиск по номеру, трекеры': [
        'Cloaked', 'Guardio', 'ClarityCheck', 'Reverse Lookup', 'Trace', 'GeoZilla (Familo / Simply Connected)',
        'Cleaner Guru / Scanguru (Universe Apps)', 'Filterly', 'KeepClean AI', 'Famio', 'Notee', 'Visify',
    ],
    'Психология, отношения, саморазвитие': [
        'Liven', 'RiseGuide (buildcharisma, intelligence)', 'ThePsychology', 'Relatio', 'Muses Academy', 'MusesAcred', 'BlossomUp',
        'BetterMe', 'Zenfy', 'Shadow Work', 'Headway', 'Nibble', 'Bitesy', 'Aligned', 'Chillio', 'KitUp', 'MyGrowth', 'Vocal Image',
        'Spilio', 'Empowered', 'Affemity', 'BeTheOneForHim', 'Feeling.me', 'Selfony', 'Growli', 'MonoBoost', 'TodayIsTheDay',
        'MellowFlow', 'Copymind', 'MyPersonalityLab', 'AliveMoment', 'Findies', 'Goodly', 'FABU', 'Wisey', 'Attainify', 'Sequel',
        ],
    'Дейтинг и ИИ-компаньоны': [
        'Honey (ИИ-девушка)', 'MyDeepChat', 'TheRealIntro', 'Taimi', 'Hily', 'Kismia', 'MeetMyAge', 'Jolly', 'GetFlirty',
        'SweetSecrets', 'Melto', 'AmourTalks', 'DatingArts', 'CharmingTalks', '(ленд без домена)', 'Astari',
    ],
    'Астрология и эзотерика': ['Hint (астрология)', 'Nebula', 'Astroline', 'Spiritual Society', 'Moonly', 'Spirio', 'Yodha'],
    'IQ, память, мозг': [
        'MyIQ', 'Mental Impulse (архетипы, IQ)', 'Testora', 'memoryOS', 'Impulse', 'CognitiveGrowth', 'Intellio', 'Selfery',
        'Memory Anthem', 'IQVerse', 'TheTestMind', 'Brain games (iOS id1599756543)',
    ],
    'ИИ-обучение, заработок с ИИ, работа': [
        'Coursiv', 'Educly', 'Skilario', 'ProMuse', 'Kodree', 'Jobescape', 'GlobalWork', 'Intch', 'Shift', 'JobLand', 'Nexera',
        'SuccessWise', 'StepLearn', 'AI Corso', 'TheGrowAI', 'Sunly AI', 'Futureproof', 'Codefinity', 'Sololearn', 'CertX AI',
        'Skillsta', 'Finestro', 'ClickTech',
    ],
    'Языки': ['Appewa (языки)', 'Jumpspeak', 'Learna AI', 'Lola Speak', 'WordsBooster', 'Wordletic', 'English Improve'],
    'Стиль и красота': ['Mosso', 'Dressly', 'Lovi', 'Luvly', 'MaxBeauty', 'Epica Beauty', 'Lumi', 'Stylio', 'Ageless'],
    'Бизнес-инструменты': ['Zeely', 'Adzi'],
    'ИИ-генерация (фото, видео, музыка, тексты)': [
        'Genius (ИИ-фото)', 'Zurna (ИИ-фото)', 'Mozart AI', 'HyperMusic AI (w2a.one)', 'Dear Melodies', 'FaceLab', 'PixTuner',
        'ReRoom AI', 'forbio',
    ],
    'Хобби и прочие сервисы': [
        'Mob (рецепты)', 'ValueScout', 'fnlfx (беттинг)', 'The Music Learner', 'GoLearnPiano', 'Hobby Skills', 'PlantIn',
        'Plant app (exclusiveplantapp)', 'GreenThumb', 'PawChamp', 'Woofz', 'RatePunk', 'SportDex', 'Rockin', 'Nikmas', 'AddMile',
    ],
    'Религия': ['AyahPath', 'Prayers Academy'],
    'Дети и родители': ['Kidology', 'Keiki', 'Education4Kids', 'Prepare4School', 'Parenting Leader'],
    'Финансы и инвестиции': ['Finelo AI', 'CoinIn', 'Subpilot', 'Pivex Funded', 'Bucksly', 'JustDone'],
    'Прочее': ['Duomo', 'Marevo'],
}
VERT = {a: v for v, apps in V.items() for a in apps}
