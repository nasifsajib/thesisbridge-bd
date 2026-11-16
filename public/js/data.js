/* ==========================================================================
   ThesisBridge BD — Dummy Data Layer
   --------------------------------------------------------------------------
   All content lives in plain JS arrays/objects so it can later be replaced
   by fetch() calls to a real API without touching the UI modules.
   ========================================================================== */

window.TB_DATA = (function () {
  'use strict';

  /* ---------------------------- Filter vocabularies --------------------- */

  const categories = [
    { name: 'Artificial Intelligence', short: 'AI', icon: 'fa-brain' },
    { name: 'Machine Learning', short: 'ML', icon: 'fa-robot' },
    { name: 'Cybersecurity', icon: 'fa-shield-halved' },
    { name: 'IoT', icon: 'fa-wifi' },
    { name: 'Software Engineering', icon: 'fa-code' },
    { name: 'Computer Vision', icon: 'fa-eye' },
    { name: 'NLP', icon: 'fa-language' },
    { name: 'Data Science', icon: 'fa-chart-bar' },
    { name: 'Networking', icon: 'fa-network-wired' }
  ];

  const difficulties = ['Beginner', 'Intermediate', 'Advanced'];
  const types = ['Thesis', 'Project', 'Review', 'Experimental'];

  // Technology filter options (spec list) + extras used by the match quiz.
  const technologies = ['Python', 'TensorFlow', 'PyTorch', 'Arduino', 'ESP32', 'Java', 'Kotlin', 'JavaScript'];
  const quizTechnologies = technologies.concat(['OpenCV', 'Flutter', 'Node.js', 'R']);

  const universities = [
    'BUET', 'University of Dhaka', 'CUET', 'KUET', 'RUET', 'SUST', 'IUT',
    'BRAC University', 'North South University', 'AIUB',
    'Daffodil International University', 'Jahangirnagar University'
  ];

  const departments = [
    'Computer Science & Engineering',
    'Electrical & Electronic Engineering',
    'Software Engineering',
    'Information Technology',
    'Statistics'
  ];

  const expertiseOptions = [
    'Python', 'TensorFlow', 'PyTorch', 'JavaScript', 'Java', 'Kotlin', 'Arduino', 'ESP32',
    'Deep Learning', 'Computer Vision', 'NLP', 'Cybersecurity', 'Data Science', 'Software Engineering'
  ];

  /* ------------------------------ Research ideas ------------------------ */

  const researchIdeas = [
    {
      id: 1,
      title: 'Explainable AI for Medical Diagnosis',
      description: 'Build deep learning diagnostic models that explain their predictions using SHAP and LIME so clinicians can trust the results.',
      category: 'Artificial Intelligence',
      area: 'Healthcare AI',
      difficulty: 'Intermediate',
      technologies: ['Python', 'PyTorch', 'Scikit-learn'],
      type: 'Thesis',
      universities: ['BUET', 'SUST', 'KUET'],
      tags: ['XAI', 'Healthcare', 'Deep Learning', 'SHAP'],
      problem: 'Deep learning models used in medical diagnosis act as black boxes — doctors cannot see why a model predicted a disease, which blocks clinical trust and adoption.',
      gap: 'Very few studies evaluate explanation faithfulness (do explanations reflect true model reasoning?) on datasets collected from Bangladeshi hospitals and patients.',
      methodology: 'Train a CNN baseline on a public medical dataset (e.g., chest X-rays), apply LIME and SHAP post-hoc explanation methods, then measure faithfulness, stability and clinician satisfaction through a small survey of doctors.',
      outcome: 'An interpretable diagnosis prototype plus a report comparing explanation methods with faithfulness metrics and clinician feedback.',
      keywords: ['Explainable AI', 'SHAP', 'LIME', 'Clinical decision support', 'Deep learning'],
      featured: 98
    },
    {
      id: 2,
      title: 'Bangla Sentiment Analysis of Social Media Posts',
      description: 'Classify public Bangla and Banglish social media posts as positive, negative or neutral using transformer-based NLP models.',
      category: 'NLP',
      area: 'Bangla NLP',
      difficulty: 'Intermediate',
      technologies: ['Python', 'TensorFlow'],
      type: 'Thesis',
      universities: ['University of Dhaka', 'Jahangirnagar University', 'SUST'],
      tags: ['Bangla NLP', 'Sentiment Analysis', 'Transformers'],
      problem: 'Brands, newsrooms and government agencies cannot measure public opinion in Bangla because most sentiment tools only support English.',
      gap: 'Low-resource Bangla sentiment benchmarks are small and rarely cover romanized "Banglish" text mixed with code-switching, dialects and noisy spelling.',
      methodology: 'Collect and manually annotate a corpus of Bangla and Banglish posts, fine-tune Bangla-BERT and simpler baselines (TF-IDF + SVM), and compare performance with proper train/test splits and error analysis.',
      outcome: 'A labeled Bangla sentiment dataset, a trained classifier with an accuracy/F1 report, and a simple demo that scores new posts.',
      keywords: ['Bangla sentiment', 'Banglish', 'BERT', 'Low-resource NLP'],
      featured: 95
    },
    {
      id: 3,
      title: 'Low-Cost Flood Early Warning System Using IoT',
      description: 'Design an ESP32/Arduino river-level monitoring network that sends SMS alerts to communities before flooding starts.',
      category: 'IoT',
      area: 'Flood Resilience',
      difficulty: 'Beginner',
      technologies: ['Arduino', 'ESP32'],
      type: 'Project',
      universities: ['CUET', 'RUET', 'KUET'],
      tags: ['Flood', 'Embedded', 'Sensors', 'Disaster Management'],
      problem: 'Communities in flood-prone districts often get only hours of warning, which is too late to protect livestock, grain and homes.',
      gap: 'Existing flood forecasting relies on expensive government sensors upstream; cheap, community-owned river-level sensing with reliable offline alerting is barely explored.',
      methodology: 'Build ultrasonic water-level sensor nodes with ESP32, send readings over GSM/Wi-Fi to a lightweight server, define threshold-based alert rules, and field-test alert latency and battery life.',
      outcome: 'A working prototype node, a dashboard of water levels, and an SMS alert pipeline demonstrated on a campus pond or drain.',
      keywords: ['IoT', 'Early warning', 'ESP32', 'Flood forecasting'],
      featured: 93
    },
    {
      id: 4,
      title: 'Deepfake Video Detection Using Temporal CNNs',
      description: 'Detect AI-manipulated face-swap videos by analysing temporal inconsistencies between frames with a CNN-LSTM pipeline.',
      category: 'Computer Vision',
      area: 'Multimedia Security',
      difficulty: 'Advanced',
      technologies: ['Python', 'PyTorch'],
      type: 'Experimental',
      universities: ['BUET', 'IUT'],
      tags: ['Deepfake', 'Forensics', 'Video Analysis'],
      problem: 'Deepfake videos are increasingly used for defamation and fraud in South Asia, and humans detect them barely better than chance.',
      gap: 'Most detectors are trained on Western celebrity face-swap datasets and degrade sharply on compressed, low-resolution videos typical of social media sharing in the region.',
      methodology: 'Train a CNN frame feature extractor combined with an LSTM over frame sequences on FaceForensics++ and DFDC, then benchmark robustness under video compression, resizing and low-light augmentation.',
      outcome: 'A trained detector with a robustness report across compression levels, plus a web demo where users upload a clip and get a manipulation score.',
      keywords: ['Deepfake detection', 'CNN-LSTM', 'Video forensics', 'Temporal analysis'],
      featured: 90
    },
    {
      id: 5,
      title: 'ML-Based Network Intrusion Detection System',
      description: 'Compare classical ML and deep learning models for detecting network intrusions on the CIC-IDS2017 dataset in real time.',
      category: 'Cybersecurity',
      area: 'Cyber Defense',
      difficulty: 'Advanced',
      technologies: ['Python', 'TensorFlow'],
      type: 'Thesis',
      universities: ['BUET', 'IUT', 'CUET'],
      tags: ['IDS', 'Network Security', 'Deep Learning'],
      problem: 'Signature-based intrusion detection systems miss zero-day attacks; university and ISP networks need anomaly-based detection that keeps up with live traffic.',
      gap: 'Published IDS models are benchmarked offline; few studies address real-time throughput, concept drift and false-alert fatigue in operational networks.',
      methodology: 'Preprocess CIC-IDS2017 flows, train and tune Random Forest, XGBoost and an autoencoder + classifier hybrid, then measure precision/recall, inference speed and drift over time splits.',
      outcome: 'A comparative study, a tuned model with feature-importance analysis, and a streaming demo that flags simulated attacks on a test network.',
      keywords: ['Intrusion detection', 'Anomaly detection', 'CIC-IDS2017', 'Network security'],
      featured: 88
    },
    {
      id: 6,
      title: 'Dhaka Traffic Flow Prediction & Visualization',
      description: 'Predict short-term traffic congestion on key Dhaka corridors from historical and weather data, visualized on an interactive map.',
      category: 'Data Science',
      area: 'Smart Cities',
      difficulty: 'Intermediate',
      technologies: ['Python', 'JavaScript'],
      type: 'Thesis',
      universities: ['BUET', 'University of Dhaka', 'AUST'],
      tags: ['Smart City', 'Time Series', 'Visualization'],
      problem: 'Commuters and city planners lack reliable short-term congestion forecasts for Dhaka, one of the world\'s most congested cities.',
      gap: 'Global traffic models are trained on disciplined highway data; mixed-traffic cities with rickshaws, buses and informal lanes break their assumptions.',
      methodology: 'Aggregate publicly available traffic-speed and weather data, engineer time-series features, compare ARIMA/SARIMA, gradient boosting and LSTM forecasts, and build a Leaflet map dashboard.',
      outcome: 'A congestion prediction model with error metrics per corridor and a public web map showing 15/30/60-minute forecasts.',
      keywords: ['Traffic prediction', 'Time series', 'LSTM', 'Smart city', 'Leaflet'],
      featured: 86
    },
    {
      id: 7,
      title: 'Face-Recognition Attendance System',
      description: 'A classroom attendance camera system that recognizes students from faces and logs attendance automatically with anti-spoofing checks.',
      category: 'Computer Vision',
      area: 'EdTech',
      difficulty: 'Beginner',
      technologies: ['Python', 'JavaScript'],
      type: 'Project',
      universities: ['AIUB', 'Daffodil International University', 'UIU'],
      tags: ['Face Recognition', 'OpenCV', 'Automation'],
      problem: 'Manual roll-call wastes 5–10 minutes of every class and proxy attendance is common in large sections.',
      gap: 'Existing demo systems fail on lighting variation, tilted faces and photo-spoofing in real classrooms — practical accuracy studies are rare.',
      methodology: 'Use OpenCV face detection with face embeddings (FaceNet/dlib), build a class roster database, add liveness checks (blink detection), and evaluate accuracy across seating positions and lighting.',
      outcome: 'A working attendance kiosk app with a roster dashboard, plus an accuracy report under real classroom conditions.',
      keywords: ['Face recognition', 'Attendance', 'OpenCV', 'Embeddings'],
      featured: 82
    },
    {
      id: 8,
      title: 'Bangla Handwritten Digit & Character Recognition',
      description: 'Recognize handwritten Bangla numerals and basic characters using CNNs on the CMATERdb / NumtaDB datasets.',
      category: 'Computer Vision',
      area: 'OCR & Document AI',
      difficulty: 'Beginner',
      technologies: ['Python', 'TensorFlow'],
      type: 'Project',
      universities: ['University of Rajshahi', 'Jahangirnagar University', 'CUET'],
      tags: ['OCR', 'Bangla', 'CNN', 'NumtaDB'],
      problem: 'Digitizing handwritten Bangla forms, postal mail and old manuscripts still requires slow manual typing.',
      gap: 'Bangla handwritten recognition accuracy drops on real-world degraded documents; most work stops at clean scanned digits.',
      methodology: 'Train CNNs of increasing depth on NumtaDB digits and CMATERdb characters, apply augmentation (noise, rotation, elasticity), and analyze per-class confusion.',
      outcome: 'A trained recognizer with per-character accuracy charts and a small web canvas where users draw a digit and get a prediction.',
      keywords: ['Bangla OCR', 'Handwriting recognition', 'CNN', 'NumtaDB'],
      featured: 80
    },
    {
      id: 9,
      title: 'Phishing Website Detection Browser Extension',
      description: 'A Chrome/Firefox extension that flags phishing pages in real time using URL and page-content features.',
      category: 'Cybersecurity',
      area: 'Web Security',
      difficulty: 'Beginner',
      technologies: ['Python', 'JavaScript'],
      type: 'Project',
      universities: ['North South University', 'BRAC University', 'Daffodil International University'],
      tags: ['Phishing', 'Browser Extension', 'Web Security'],
      problem: 'Phishing is the most common first step of cyberattacks targeting students and small businesses in Bangladesh, and victims rarely notice fake domains.',
      gap: 'Academic phishing detectors report accuracy but almost none ship as usable, low-latency browser extensions evaluated on live browsing.',
      methodology: 'Train a gradient-boosted classifier on URL lexical, host and page-content features (PhishTank / UCI phish dataset), export to a browser extension that scores pages in real time, and measure latency plus false positives on popular sites.',
      outcome: 'A published-able extension prototype, a model card with accuracy/precision/recall, and a user study with 10+ testers.',
      keywords: ['Phishing detection', 'Browser extension', 'URL features', 'XGBoost'],
      featured: 79
    },
    {
      id: 10,
      title: 'Smart Irrigation Controller with ESP32',
      description: 'An ESP32 soil-moisture-controlled irrigation system that waters crops only when needed and reports usage to a mobile dashboard.',
      category: 'IoT',
      area: 'Smart Agriculture',
      difficulty: 'Beginner',
      technologies: ['ESP32', 'Arduino'],
      type: 'Project',
      universities: ['BAU', 'KUET', 'SUST'],
      tags: ['Agriculture', 'Embedded', 'Water Saving'],
      problem: 'Farmers irrigate on fixed schedules and over-water, wasting groundwater and fuel during the dry season.',
      gap: 'Commercial smart irrigation is too expensive for smallholder farms; open, low-cost controllers validated on Bangladeshi soil and crops are missing.',
      methodology: 'Calibrate capacitive soil-moisture sensors, build a threshold + forecast control loop on ESP32, log water usage to a cloud dashboard, and run a greenhouse/pot comparison against scheduled watering.',
      outcome: 'A sub-$25 controller prototype, a usage dashboard, and a measured water-saving percentage versus a control group.',
      keywords: ['Smart irrigation', 'ESP32', 'Soil moisture', 'Precision agriculture'],
      featured: 78
    },
    {
      id: 11,
      title: 'Predicting Student Performance with Machine Learning',
      description: 'Predict semester GPA and dropout risk from LMS activity, attendance and previous results to trigger early support.',
      category: 'Machine Learning',
      area: 'Learning Analytics',
      difficulty: 'Beginner',
      technologies: ['Python'],
      type: 'Thesis',
      universities: ['University of Dhaka', 'Jahangirnagar University', 'RUET'],
      tags: ['Education', 'Prediction', 'LMS Data'],
      problem: 'Departments identify struggling students only after midterm results, when recovery is already hard.',
      gap: 'Learning-analytics models are mostly trained on Western MOOC data; private university LMS data from Bangladesh with proper privacy handling is almost unstudied.',
      methodology: 'Anonymize LMS logs, attendance and past grades; compare logistic regression, random forest and gradient boosting; evaluate with cross-validation and fairness checks across sections.',
      outcome: 'An early-warning model with interpretable feature importance and a mock advisor dashboard showing at-risk students.',
      keywords: ['Learning analytics', 'Dropout prediction', 'Early warning', 'Educational data mining'],
      featured: 77
    },
    {
      id: 12,
      title: 'Blockchain-Based E-Voting System',
      description: 'A permissioned blockchain voting prototype that keeps an immutable, independently verifiable ballot record.',
      category: 'Cybersecurity',
      area: 'Trust & Security',
      difficulty: 'Advanced',
      technologies: ['Java', 'JavaScript'],
      type: 'Project',
      universities: ['BUET', 'IUT', 'KUET'],
      tags: ['Blockchain', 'E-Voting', 'Cryptography'],
      problem: 'Student union and committee elections still use paper or simple web polls that are easy to dispute and hard to audit.',
      gap: 'Most e-voting prototypes sacrifice either ballot secrecy or verifiability; practical deployments for small organizations are rarely reported end-to-end.',
      methodology: 'Design a permissioned chain (Hyperledger Fabric or a simple Java chain), implement voter registration, blind-signed ballots and a verification path, then test integrity under simulated malicious nodes.',
      outcome: 'A working election prototype with a voter walkthrough, an auditor verification tool, and a security analysis chapter.',
      keywords: ['Blockchain', 'E-voting', 'Blind signature', 'Auditability'],
      featured: 75
    },
    {
      id: 13,
      title: 'Microservices vs Monolith: A Performance Case Study',
      description: 'Empirically compare response time, scaling and failure behaviour of the same app built as a monolith and as microservices.',
      category: 'Software Engineering',
      area: 'Software Architecture',
      difficulty: 'Intermediate',
      technologies: ['Java', 'JavaScript'],
      type: 'Experimental',
      universities: ['BUET', 'North South University', 'IUT'],
      tags: ['Microservices', 'Benchmarking', 'Architecture'],
      problem: 'Teams adopt microservices on hype without local evidence of throughput or operational cost for small-scale systems.',
      gap: 'Published comparisons use toy apps or cloud-scale workloads; controlled experiments at typical Bangladeshi startup scale are scarce.',
      methodology: 'Implement the same course-management app twice (Spring monolith vs REST microservices with a gateway), drive identical load tests with JMeter, and measure latency, CPU/memory, scaling behaviour and failure recovery.',
      outcome: 'A rigorous empirical report with reproducible load-test scripts and guidelines for when microservices pay off.',
      keywords: ['Microservices', 'Monolith', 'Load testing', 'Scalability', 'JMeter'],
      featured: 72
    },
    {
      id: 14,
      title: 'Bangla Voice Assistant for Farmers',
      description: 'A speech-enabled Android assistant that answers common agriculture questions in Bangla, working with low-end phones.',
      category: 'NLP',
      area: 'Speech & Language',
      difficulty: 'Advanced',
      technologies: ['Python', 'TensorFlow'],
      type: 'Project',
      universities: ['BAU', 'University of Dhaka', 'SUST'],
      tags: ['Speech Recognition', 'Bangla', 'Agriculture', 'Android'],
      problem: 'Smallholder farmers cannot access advisory services because helplines are overloaded and literacy barriers exclude text services.',
      gap: 'Bangla speech recognition research targets clean read-aloud audio; spontaneous farm-field speech with noise has no practical assistant built on it.',
      methodology: 'Fine-tune a Bangla ASR model (e.g., wav2vec2) on public + self-collected audio, build an intent-matching FAQ layer over agriculture extension content, and deploy an offline-first Android client.',
      outcome: 'A working voice QA prototype answering 50+ common questions with measured word error rate under noisy audio.',
      keywords: ['Speech recognition', 'Bangla ASR', 'Voice assistant', 'wav2vec2'],
      featured: 71
    },
    {
      id: 15,
      title: 'Systematic Review: ML for Crop Disease Detection',
      description: 'A structured literature review of machine-learning crop disease detection studies in South Asia (2015–2025).',
      category: 'Machine Learning',
      area: 'Smart Agriculture',
      difficulty: 'Beginner',
      technologies: ['Python', 'TensorFlow'],
      type: 'Review',
      universities: ['BAU', 'SUST', 'HSTU'],
      tags: ['Systematic Review', 'Agriculture', 'Plant Disease'],
      problem: 'Hundreds of crop-disease CNN papers exist, but researchers entering the field have no structured map of what works and what is missing.',
      gap: 'Existing reviews rarely follow PRISMA protocol or quantify the field-vs-lab dataset gap that limits real deployment in South Asia.',
      methodology: 'Follow PRISMA: search IEEE, Springer, Scopus and Google Scholar with defined queries, screen studies against inclusion criteria, extract datasets, methods and reported accuracy, and synthesize trends.',
      outcome: 'A PRISMA-compliant review paper draft with tables of datasets/methods and a research agenda for field-deployable models.',
      keywords: ['Systematic review', 'PRISMA', 'Crop disease', 'CNN', 'Plant pathology'],
      featured: 70
    },
    {
      id: 16,
      title: 'Low-Bandwidth Adaptive Video Streaming',
      description: 'Implement and evaluate adaptive bitrate algorithms that keep video smooth on weak and fluctuating mobile networks.',
      category: 'Networking',
      area: 'Future Networks',
      difficulty: 'Advanced',
      technologies: ['Python', 'JavaScript'],
      type: 'Experimental',
      universities: ['BUET', 'CUET', 'KUET'],
      tags: ['Video Streaming', 'QoE', 'ABR', 'QUIC'],
      problem: 'Students attend online classes over unstable mobile internet where standard adaptive streaming still stalls and downshifts aggressively.',
      gap: 'Bandwidth-estimation ABR rules are tuned for 4G/5G averages; the "sawtooth" connectivity pattern of rural mobile networks is under-modelled.',
      methodology: 'Set up a dash.js / ExoPlayer testbed, replay recorded 3G/4G throughput traces from Bangladeshi networks, compare buffer-based and learning-based ABR policies on rebuffer ratio and average bitrate.',
      outcome: 'An open testbed with network traces, a comparative QoE study, and a recommended ABR configuration for e-learning platforms.',
      keywords: ['Adaptive bitrate', 'DASH', 'Quality of experience', 'Network traces'],
      featured: 68
    },
    {
      id: 17,
      title: 'Fake News Detection in Bangla Media',
      description: 'Detect fake and misleading Bangla news articles using linguistic features and pre-trained language models.',
      category: 'NLP',
      area: 'Misinformation',
      difficulty: 'Intermediate',
      technologies: ['Python', 'PyTorch'],
      type: 'Thesis',
      universities: ['University of Dhaka', 'Jahangirnagar University', 'BRAC University'],
      tags: ['Fake News', 'Bangla NLP', 'Classification'],
      problem: 'Misleading Bangla news spreads fast on Facebook and WhatsApp, and fact-checkers cannot keep up manually.',
      gap: 'Bangla fake-news datasets are tiny and skewed toward politics; cross-domain generalization (training on politics, testing on health) is almost unmeasured.',
      methodology: 'Build an annotated corpus from fact-checking sites and mainstream news, fine-tune Bangla-BERT with stylistic and source features, and run cross-domain experiments with detailed error analysis.',
      outcome: 'A dataset, a baseline model with cross-domain results, and a browser demo that scores pasted article text.',
      keywords: ['Fake news', 'Misinformation', 'Bangla BERT', 'Fact-checking'],
      featured: 67
    },
    {
      id: 18,
      title: 'Energy-Efficient Routing in Wireless Sensor Networks',
      description: 'Simulate and compare routing protocols that extend WSN battery life for environmental monitoring deployments.',
      category: 'Networking',
      area: 'Wireless Networks',
      difficulty: 'Intermediate',
      technologies: ['Python', 'ESP32'],
      type: 'Thesis',
      universities: ['KUET', 'RUET', 'CUET'],
      tags: ['WSN', 'Routing', 'Energy', 'Simulation'],
      problem: 'Sensor nodes die within weeks in field deployments, and replacing batteries across a river or forest sensor network is costly.',
      gap: 'Classical LEACH-family protocols are tested with idealized radio models; validation against measured ESP32 power draw is rare.',
      methodology: 'Measure real ESP32 current draw for transmit/sleep states, feed the numbers into an NS-3 or custom Python simulator, and compare LEACH, PEGASIS and a proposed threshold variant on network lifetime.',
      outcome: 'A calibrated simulation study linking measured hardware power profiles to protocol lifetime predictions.',
      keywords: ['WSN', 'LEACH', 'Energy efficiency', 'NS-3', 'Lifetime analysis'],
      featured: 65
    },
    {
      id: 19,
      title: 'Mental Health Companion Chatbot for Students',
      description: 'A rule-plus-retrieval chatbot app that offers coping exercises and routes students to counseling resources.',
      category: 'Artificial Intelligence',
      area: 'Digital Health',
      difficulty: 'Intermediate',
      technologies: ['Python', 'Kotlin'],
      type: 'Project',
      universities: ['University of Dhaka', 'BRAC University', 'North South University'],
      tags: ['Chatbot', 'Mental Health', 'Mobile App', 'HCI'],
      problem: 'Campus counseling services are understaffed and stigmatized, so most students never seek help during stressful periods.',
      gap: 'Mental-health chatbots are built for English-speaking users; culturally adapted, privacy-first Bangla/English chatbots for universities are missing.',
      methodology: 'Co-design scripts with counselors, implement intent handling plus a retrieval layer over approved content, build an Android client with local data storage, and run a usability + safety review.',
      outcome: 'A pilot chatbot app with a safety protocol, counselor-approved content base, and usability results from student testers.',
      keywords: ['Chatbot', 'Mental health', 'Conversational AI', 'Android', 'Digital wellbeing'],
      featured: 74
    },
    {
      id: 20,
      title: 'Accessibility-First University Management System',
      description: 'Rebuild a course registration portal following WCAG 2.1 AA with screen-reader and keyboard-first usability testing.',
      category: 'Software Engineering',
      area: 'HCI & Accessibility',
      difficulty: 'Beginner',
      technologies: ['JavaScript', 'Java'],
      type: 'Project',
      universities: ['Jahangirnajar University', 'Daffodil International University', 'AIUB'],
      tags: ['Accessibility', 'WCAG', 'Web App', 'Usability'],
      problem: 'University portals in Bangladesh are notoriously unusable for students with visual or motor disabilities, blocking course registration entirely.',
      gap: 'Accessibility research in the region focuses on news sites; enterprise-style university systems have never been audited and re-engineered end-to-end.',
      methodology: 'Audit an existing portal with axe/WAVE and screen-reader walkthroughs, rebuild key flows (login, registration, results) to WCAG 2.1 AA, and measure task success with disabled-student testers.',
      outcome: 'An open-source accessible portal module plus a before/after audit report with task-completion metrics.',
      keywords: ['Accessibility', 'WCAG 2.1', 'Screen reader', 'Usability testing', 'Inclusive design'],
      featured: 63
    }
  ];

  /* ------------------------------- Supervisors --------------------------- */

  const supervisors = [
    {
      id: 1,
      name: 'Dr. Ahmed Rahman',
      title: 'Professor',
      university: 'BUET',
      department: 'Computer Science & Engineering',
      interests: ['AI', 'NLP', 'Machine Learning'],
      expertise: ['Python', 'PyTorch', 'TensorFlow', 'Deep Learning', 'NLP', 'Data Science'],
      areas: ['Artificial Intelligence', 'Machine Learning', 'NLP'],
      publications: 118,
      supervisionTypes: ['Thesis', 'Review', 'Experimental'],
      accepting: true,
      email: 'a.rahman@demo.tb-bd.edu',
      office: 'CSE Building, Room 402',
      bio: 'Leads the Intelligent Systems Lab and has supervised 60+ undergraduate theses on language and healthcare AI. Prefers students who read papers before knocking on his door.',
      selectedPubs: [
        'Explainable deep learning for diabetic retinopathy screening — Journal of Biomedical Informatics (2023)',
        'Bangla topic modelling with neural document embeddings — ACL Anthology, WNLP Workshop (2022)',
        'A survey of low-resource NLP for South Asian languages — ACM Computing Surveys (2021)'
      ],
      supervisionAreas: [
        'Undergraduate thesis (CSE 4000) on applied machine learning',
        'Systematic reviews and survey papers with final-year students',
        'Experimental studies in the Intelligent Systems Lab'
      ],
      suggestedTopics: [
        'Explainable AI for medical diagnosis in low-resource clinics',
        'Retrieval-augmented question answering over Bangla documents',
        'Efficient fine-tuning of language models on a single GPU'
      ]
    },
    {
      id: 2,
      name: 'Dr. Farhana Karim',
      title: 'Associate Professor',
      university: 'University of Dhaka',
      department: 'Computer Science & Engineering',
      interests: ['NLP', 'HCI', 'Bangla Language Technology'],
      expertise: ['Python', 'TensorFlow', 'NLP', 'Data Science'],
      areas: ['NLP', 'Artificial Intelligence', 'Software Engineering'],
      publications: 74,
      supervisionTypes: ['Thesis', 'Project', 'Experimental'],
      accepting: true,
      email: 'f.karim@demo.tb-bd.edu',
      office: 'Science Complex, Room 215',
      bio: 'Studies how people actually use language technology — from Bangla keyboard apps to voice interfaces — and publishes with student co-authors every year.',
      selectedPubs: [
        'Typing behaviour of Bangla mobile users on predictive keyboards — CHI IND (2023)',
        'Code-switching detection in Bangla-English social media — LREC (2022)',
        'Design lessons from deploying a Bangla spelling checker — ACM HCI journal (2021)'
      ],
      supervisionAreas: [
        'Thesis and project supervision in NLP and HCI',
        'Usability and deployment studies with real users',
        'Inclusive language technology for low-literacy users'
      ],
      suggestedTopics: [
        'Bangla sentiment analysis of social media posts',
        'Voice interfaces for public service information kiosks',
        'Keyboard prediction quality for Banglish typing'
      ]
    },
    {
      id: 3,
      name: 'Prof. Dr. Md. Kamal Uddin',
      title: 'Professor',
      university: 'CUET',
      department: 'Electrical & Electronic Engineering',
      interests: ['IoT', 'Wireless Networks', 'Embedded Systems'],
      expertise: ['Arduino', 'ESP32', 'Software Engineering'],
      areas: ['IoT', 'Networking'],
      publications: 96,
      supervisionTypes: ['Thesis', 'Project'],
      accepting: false,
      email: 'kamal@demo.tb-bd.edu',
      office: 'EEE Building, Room 108',
      bio: 'Runs the embedded systems lab with a long-running river-sensor testbed. Expects hardware students to solder their own prototypes before asking for lab access.',
      selectedPubs: [
        'River-level sensing network for coastal flood warning — IEEE Sensors Journal (2023)',
        'Energy harvesting for ESP32 sensor nodes in monsoon conditions — Elsevier IoT (2022)',
        'A decade of WSN deployments in Bangladesh: lessons learned — IEEE Access (2020)'
      ],
      supervisionAreas: [
        'Final-year design projects on sensor networks',
        'IoT thesis topics with field deployment components',
        'Embedded systems prototyping and testing'
      ],
      suggestedTopics: [
        'Low-cost flood early warning system using IoT',
        'Energy-efficient routing in wireless sensor networks',
        'Solar-powered weather stations for tea gardens'
      ]
    },
    {
      id: 4,
      name: 'Dr. Nusrat Jahan',
      title: 'Assistant Professor',
      university: 'BRAC University',
      department: 'Computer Science & Engineering',
      interests: ['Computer Vision', 'Medical Imaging', 'ML'],
      expertise: ['Python', 'PyTorch', 'TensorFlow', 'Computer Vision', 'Deep Learning'],
      areas: ['Computer Vision', 'Machine Learning', 'Artificial Intelligence'],
      publications: 41,
      supervisionTypes: ['Thesis', 'Project', 'Experimental'],
      accepting: true,
      email: 'n.jahan@demo.tb-bd.edu',
      office: 'Building 2, Room 610',
      bio: 'Works on medical image analysis with two local hospitals and maintains a public annotated retinal image dataset. Meets thesis students weekly in structured sprints.',
      selectedPubs: [
        'Retinal vessel segmentation under domain shift — ISBI (2023)',
        'Low-data augmentation strategies for medical imaging — Computerized Medical Imaging and Graphics (2022)',
        'Crowdsourcing image labels with Bangla-speaking annotators — MICCAI workshop (2021)'
      ],
      supervisionAreas: [
        'Vision thesis topics with hospital data partnerships',
        'Experiment-driven projects with rigorous baselines',
        'Student internships in the medical imaging lab'
      ],
      suggestedTopics: [
        'Deepfake video detection using temporal CNNs',
        'Bangla handwritten digit and character recognition',
        'Chest X-ray classification with noisy labels'
      ]
    },
    {
      id: 5,
      name: 'Dr. Md. Tanvir Hasan',
      title: 'Associate Professor',
      university: 'SUST',
      department: 'Computer Science & Engineering',
      interests: ['Data Science', 'AI', 'Smart Cities'],
      expertise: ['Python', 'TensorFlow', 'Data Science', 'Deep Learning'],
      areas: ['Data Science', 'Artificial Intelligence', 'Machine Learning'],
      publications: 63,
      supervisionTypes: ['Thesis', 'Project', 'Review'],
      accepting: true,
      email: 'tanvir@demo.tb-bd.edu',
      office: 'Academic Building C, Room 312',
      bio: 'Analyzes urban mobility and air-quality data from Sylhet; strong believer in open data and reproducible notebooks. Requires a GitHub portfolio from applicants.',
      selectedPubs: [
        'Spatio-temporal air quality prediction with graph neural networks — Environmental Modelling & Software (2023)',
        'Bus travel time reliability in a developing-world city — Transportation Research Record (2022)',
        'Open urban dashboards for medium-size cities — Governance Information Quarterly (2021)'
      ],
      supervisionAreas: [
        'Data science theses on urban or environmental datasets',
        'Project supervision for data-driven civic apps',
        'Review papers on applied urban analytics'
      ],
      suggestedTopics: [
        'Dhaka traffic flow prediction and visualization',
        'Air quality forecasting with low-cost sensor fusion',
        'Ride-sharing demand analysis for campus shuttles'
      ]
    },
    {
      id: 6,
      name: 'Dr. Rezaul Islam',
      title: 'Professor',
      university: 'KUET',
      department: 'Computer Science & Engineering',
      interests: ['Cybersecurity', 'Cryptography', 'Network Security'],
      expertise: ['Java', 'Python', 'Cybersecurity'],
      areas: ['Cybersecurity', 'Networking'],
      publications: 102,
      supervisionTypes: ['Thesis', 'Review', 'Experimental'],
      accepting: true,
      email: 'rezaul@demo.tb-bd.edu',
      office: 'CSE Building, Room 305',
      bio: 'Heads the security research group, consults for banks on payment security, and has a strict rule: no blockchain thesis without a real deployment story.',
      selectedPubs: [
        'A taxonomy of mobile financial service fraud in Bangladesh — Computers & Security (2023)',
        'Lightweight authentication for constrained IoT devices — IEEE IoT Journal (2022)',
        'Ten years of phishing against .bd domains — ACM TOPS (2020)'
      ],
      supervisionAreas: [
        'Security-focused thesis and review supervision',
        'Applied cryptography experiments in the security lab',
        'Industry-linked projects with banking partners'
      ],
      suggestedTopics: [
        'ML-based network intrusion detection system',
        'Blockchain-based e-voting for campus elections',
        'Phishing website detection browser extension'
      ]
    },
    {
      id: 7,
      name: 'Dr. Sharmin Akter',
      title: 'Assistant Professor',
      university: 'North South University',
      department: 'Computer Science & Engineering',
      interests: ['Software Engineering', 'AI for Code', 'DevOps'],
      expertise: ['Java', 'JavaScript', 'Python', 'Software Engineering', 'Kotlin'],
      areas: ['Software Engineering', 'Artificial Intelligence'],
      publications: 38,
      supervisionTypes: ['Thesis', 'Project', 'Experimental'],
      accepting: true,
      email: 'sharmin.akter@demo.tb-bd.edu',
      office: 'Level 6, Room S-614',
      bio: 'Researches how AI tools change developer productivity in student teams, and co-runs the university hackathon. Happy to supervise first-time researchers.',
      selectedPubs: [
        'Code review latency in student project teams — ICSE SEET (2023)',
        'Do AI code assistants help novice programmers? A controlled study — ACM TOCE (2023)',
        'CI/CD adoption barriers in South Asian startups — ESEM (2021)'
      ],
      supervisionAreas: [
        'Empirical software engineering theses',
        'Developer-tool projects with user studies',
        'Experiments on AI-assisted programming education'
      ],
      suggestedTopics: [
        'Microservices vs monolith: a performance case study',
        'Mental health companion chatbot for students',
        'AI code-review bots for beginner programmers'
      ]
    },
    {
      id: 8,
      name: 'Dr. Mahmudul Hasan',
      title: 'Associate Professor',
      university: 'IUT',
      department: 'Computer Science & Engineering',
      interests: ['Cybersecurity', 'IoT Security', 'Digital Forensics'],
      expertise: ['Python', 'Java', 'Cybersecurity', 'Arduino', 'ESP32'],
      areas: ['Cybersecurity', 'IoT'],
      publications: 57,
      supervisionTypes: ['Thesis', 'Project', 'Experimental'],
      accepting: false,
      email: 'm.hasan@demo.tb-bd.edu',
      office: 'CSE Block B, Room 210',
      bio: 'Runs the forensics lab used by law-enforcement training programs; currently on research leave until December but reviews project proposals by email.',
      selectedPubs: [
        'Firmware vulnerability scanning for consumer IoT devices — ACM DTRAP (2023)',
        'Anti-forensic techniques in mobile messaging apps — Forensic Science International: Digital Investigation (2022)',
        'Securing smart campus deployments — IEEE IoT-XXS (2021)'
      ],
      supervisionAreas: [
        'IoT security theses with lab testbeds',
        'Forensics projects with real case studies',
        'Experimental security measurement studies'
      ],
      suggestedTopics: [
        'Vulnerability analysis of smart home devices sold locally',
        'Android app forensics for evidence recovery',
        'Attack detection for campus IoT networks'
      ]
    },
    {
      id: 9,
      name: 'Dr. Sadia Afrin',
      title: 'Assistant Professor',
      university: 'University of Dhaka',
      department: 'Statistics',
      interests: ['Statistical Learning', 'Biostatistics', 'Survey Methods'],
      expertise: ['Python', 'Data Science'],
      areas: ['Data Science', 'Machine Learning'],
      publications: 34,
      supervisionTypes: ['Thesis', 'Review'],
      accepting: true,
      email: 'sadia@demo.tb-bd.edu',
      office: 'Arts Building, Room 118',
      bio: 'Bridges statistics and machine learning for public-health studies, and co-authors national survey reports. Insists on honest confidence intervals.',
      selectedPubs: [
        'Sample size illusions in local health surveys — Journal of Applied Statistics (2023)',
        'Interpretable risk models for non-communicable diseases — BMC Public Health (2022)',
        'When cross-validation lies: pitfalls in small-n studies — The American Statistician (2021)'
      ],
      supervisionAreas: [
        'Statistics theses with real survey data',
        'Methodological reviews of ML evaluation practice',
        'Collaborative analysis for public-health researchers'
      ],
      suggestedTopics: [
        'Predicting student performance with machine learning',
        'Small-area estimation of poverty from satellite data',
        'Evaluation practices in applied ML papers: a review'
      ]
    },
    {
      id: 10,
      name: 'Prof. Dr. Abdul Bari',
      title: 'Professor',
      university: 'RUET',
      department: 'Electrical & Electronic Engineering',
      interests: ['Networking', 'Network Security', 'Wireless Communication'],
      expertise: ['Python', 'Cybersecurity', 'Software Engineering'],
      areas: ['Networking', 'Cybersecurity', 'IoT'],
      publications: 89,
      supervisionTypes: ['Thesis', 'Project', 'Review'],
      accepting: true,
      email: 'abari@demo.tb-bd.edu',
      office: 'EEE Building, Room 201',
      bio: 'Twenty years of teaching communication engineering; currently studies how rural mobile network traces differ from textbook models.',
      selectedPubs: [
        'Throughput traces from rural 4G networks in Bangladesh — Computer Networks (2023)',
        'Measurement study of campus Wi-Fi congestion — Computer Communications (2022)',
        'QoE of video lectures on weak links — IEEE Access (2021)'
      ],
      supervisionAreas: [
        'Networking theses with measurement campaigns',
        'Simulation plus field-test hybrid projects',
        'Review papers on wireless QoE'
      ],
      suggestedTopics: [
        'Low-bandwidth adaptive video streaming',
        'Energy-efficient routing in wireless sensor networks',
        'Wi-Fi 6 congestion in dense classrooms'
      ]
    },
    {
      id: 11,
      name: 'Dr. Ishrat Jahan Lima',
      title: 'Assistant Professor',
      university: 'Daffodil International University',
      department: 'Software Engineering',
      interests: ['Software Engineering', 'HCI', 'Accessibility'],
      expertise: ['JavaScript', 'Java', 'Software Engineering'],
      areas: ['Software Engineering'],
      publications: 29,
      supervisionTypes: ['Thesis', 'Project'],
      accepting: true,
      email: 'ishrat.lima@demo.tb-bd.edu',
      office: 'D Main Building, Room 507',
      bio: 'Leads the inclusive-design studio and audits public-sector websites for accessibility. Welcomes teams that test with real users, not just classmates.',
      selectedPubs: [
        'Accessibility barriers in government portal forms — Universal Access in the Information Society (2023)',
        'Screen-reader usability of local e-commerce checkout — Interacting with Computers (2022)',
        'Teaching accessibility in SE curricula: a case study — ACM SIGCSE (2021)'
      ],
      supervisionAreas: [
        'Accessibility-focused software projects',
        'Usability theses with disabled participants',
        'Industry projects with local UX agencies'
      ],
      suggestedTopics: [
        'Accessibility-first university management system',
        'Voice-controlled course registration for motor-impaired students',
        'WCAG audit toolchain for Bengali websites'
      ]
    },
    {
      id: 12,
      name: 'Dr. Mizanur Rahman',
      title: 'Associate Professor',
      university: 'Jahangirnagar University',
      department: 'Computer Science & Engineering',
      interests: ['NLP', 'AI', 'Digital Libraries'],
      expertise: ['Python', 'PyTorch', 'NLP', 'Deep Learning', 'Data Science'],
      areas: ['NLP', 'Artificial Intelligence', 'Data Science'],
      publications: 52,
      supervisionTypes: ['Thesis', 'Project', 'Review'],
      accepting: true,
      email: 'mizan@demo.tb-bd.edu',
      office: 'CSE Annex, Room 12',
      bio: 'Builds search and archive systems for Bangla historical texts and supervises the department reading group every Thursday.',
      selectedPubs: [
        'OCR post-correction for historical Bangla prints — ACM JOCCH (2023)',
        'Domain-specific embeddings for Bangla legal text — Information Processing & Management (2022)',
        'Named entity recognition for Bangla news — LREC (2020)'
      ],
      supervisionAreas: [
        'NLP theses on corpora and archives',
        'Digital-library software projects',
        'Survey papers on Bangla language technology'
      ],
      suggestedTopics: [
        'Fake news detection in Bangla media',
        'Search and summarization for court judgment archives',
        'A 50-year retrospective of Bangla newspaper NLP'
      ]
    }
  ];

  /* ------------------------------- Resources ----------------------------- */

  const resources = [
    {
      id: 1,
      title: 'Research Methodology 101',
      category: 'Research Methodology',
      type: 'Guide',
      typeIcon: 'fa-book-open',
      level: 'Beginner',
      minutes: 12,
      description: 'The difference between a research question, objective and hypothesis — and how to write each one.',
      details: 'Walks through the anatomy of a research project: background, problem statement, objectives, methodology and evaluation. Includes a worked example for a computer science thesis and a checklist to test whether your question is actually researchable.',
      learnPoints: ['Turn a vague topic into a focused research question', 'Write 3–5 measurable objectives', 'Choose between thesis, project and review formats'],
      url: null,
      tags: ['Methodology', 'Getting started', 'Thesis']
    },
    {
      id: 2,
      title: 'How to Read a Research Paper',
      category: 'Literature Review',
      type: 'Guide',
      typeIcon: 'fa-book-open',
      level: 'Beginner',
      minutes: 10,
      description: 'A three-pass reading strategy so you can understand any paper without reading every word.',
      details: 'The three-pass method: first pass for structure and context (5–10 min), second pass for arguments and evidence, third pass for virtually re-implementing the work. Also covers how to take notes that survive until thesis writing.',
      learnPoints: ['Read papers 3× faster with the three-pass method', 'Extract the contribution and limitation of any paper', 'Build a note system that feeds your literature review'],
      url: null,
      tags: ['Reading', 'Papers', 'Study skills']
    },
    {
      id: 3,
      title: 'Literature Review Starter Kit',
      category: 'Literature Review',
      type: 'Template',
      typeIcon: 'fa-clipboard-list',
      level: 'Beginner',
      minutes: 15,
      description: 'A synthesis matrix and review outline you can copy into Google Docs or Word today.',
      details: 'Contains a 5-column synthesis matrix (citation, method, dataset, findings, gap) and a chapter outline with sentence starters for each section. Filled in with one example row so you can see how synthesis differs from summarizing.',
      learnPoints: ['Fill a synthesis matrix for 20 papers quickly', 'Structure a review chapter paragraph by paragraph', 'Avoid the "list of summaries" trap'],
      url: null,
      tags: ['Template', 'Literature review', 'Writing']
    },
    {
      id: 4,
      title: 'Finding Your Research Gap',
      category: 'Research Gap',
      type: 'Guide',
      typeIcon: 'fa-magnifying-glass',
      level: 'Intermediate',
      minutes: 14,
      description: 'Six reliable places where research gaps hide — from limitations sections to "future work" paragraphs.',
      details: 'Gaps are rarely labelled. This guide shows where to look: limitations sections, contradictory results between papers, methods transferred to new domains, underserved populations (very common in Bangladeshi contexts), outdated benchmarks and unstudied combinations.',
      learnPoints: ['Mine "future work" and "limitations" sections systematically', 'Turn a gap into a defensible problem statement', 'Validate that your gap is real using citation tracing'],
      url: null,
      tags: ['Research gap', 'Problem statement', 'Ideas']
    },
    {
      id: 5,
      title: 'Research Gap Worksheet',
      category: 'Research Gap',
      type: 'Template',
      typeIcon: 'fa-clipboard-list',
      level: 'Beginner',
      minutes: 8,
      description: 'A one-page worksheet that compresses 10 papers into a single gap statement.',
      details: 'The worksheet asks: What is known? What is unclear? Why does it matter here? What could I actually do? Answering these four questions forces a gap statement your supervisor can evaluate in one meeting.',
      learnPoints: ['Draft a gap statement in under 30 minutes', 'Stress-test your gap before meeting a supervisor', 'Link the gap to a feasible methodology'],
      url: null,
      tags: ['Worksheet', 'Research gap', 'Planning']
    },
    {
      id: 6,
      title: 'Academic Writing Structure',
      category: 'Academic Writing',
      type: 'Guide',
      typeIcon: 'fa-book-open',
      level: 'Intermediate',
      minutes: 16,
      description: 'Paragraph shapes, tense rules and the "hourglass" structure of a strong thesis chapter.',
      details: 'Covers the hourglass model (broad to narrow to broad), the PEEL paragraph pattern for arguments, when to use past vs present tense, and transition phrases that don\'t sound robotic. Includes before/after rewrites of a typical student paragraph.',
      learnPoints: ['Structure any chapter with the hourglass model', 'Fix tense errors that markers always notice', 'Write paragraphs with one job each'],
      url: null,
      tags: ['Writing', 'Structure', 'Thesis']
    },
    {
      id: 7,
      title: 'Thesis Writing Survival Guide',
      category: 'Academic Writing',
      type: 'Guide',
      typeIcon: 'fa-book-open',
      level: 'Intermediate',
      minutes: 18,
      description: 'A chapter-by-chapter plan for writing a full undergraduate thesis in 12 weeks.',
      details: 'A realistic 12-week schedule from proposal to submission, with weekly word targets, the "write the easy chapters first" strategy, and how to handle supervisor feedback rounds without rewriting everything from scratch.',
      learnPoints: ['Plan thesis writing week by week', 'Separate drafting from editing to write faster', 'Manage supervisor feedback cycles productively'],
      url: null,
      tags: ['Thesis', 'Planning', 'Writing']
    },
    {
      id: 8,
      title: 'IEEE Citation Style Guide',
      category: 'Citation',
      type: 'Guide',
      typeIcon: 'fa-quote-right',
      level: 'Beginner',
      minutes: 9,
      description: 'How to cite papers, websites, datasets and tools in IEEE style — with copyable examples.',
      details: 'Numbered citation format used by most CSE departments and IEEE journals: in-text numbers, reference list ordering, and formats for journal articles, conference papers, books, websites, datasets and software. Ends with the five most common citation mistakes.',
      learnPoints: ['Format IEEE references for every source type', 'Cite datasets and code correctly', 'Avoid the 5 most common IEEE citation errors'],
      url: null,
      tags: ['IEEE', 'Citation', 'Formatting']
    },
    {
      id: 9,
      title: 'APA 7 Quick Reference',
      category: 'Citation',
      type: 'Guide',
      typeIcon: 'fa-quote-right',
      level: 'Beginner',
      minutes: 8,
      description: 'Author–date citations made simple, for departments and journals that use APA style.',
      details: 'Covers in-text citations for one, two and 3+ authors, reference list formats for the main source types, DOI formatting and the rules for citing secondary sources. Includes a decision flowchart for tricky cases.',
      learnPoints: ['Master APA 7 in-text citation patterns', 'Build a reference list without a generator', 'Format DOIs and URLs correctly'],
      url: null,
      tags: ['APA', 'Citation', 'Formatting']
    },
    {
      id: 10,
      title: 'Zotero Reference Manager',
      category: 'Citation',
      type: 'Tool',
      typeIcon: 'fa-screwdriver-wrench',
      level: 'Beginner',
      minutes: 6,
      description: 'Free, open-source tool that collects papers and generates citations in Word or Google Docs.',
      details: 'Install the browser connector, save papers with one click, organize them into collections per thesis chapter, and auto-generate bibliographies in IEEE or APA style. This card links to the official site.',
      learnPoints: ['Save and organize sources automatically', 'Generate formatted bibliographies instantly', 'Sync your library across devices for free'],
      url: 'https://www.zotero.org/',
      tags: ['Zotero', 'Tool', 'References']
    },
    {
      id: 11,
      title: 'Statistics for Research: The Essentials',
      category: 'Statistics',
      type: 'Guide',
      typeIcon: 'fa-book-open',
      level: 'Intermediate',
      minutes: 20,
      description: 'The 20% of statistics that covers 80% of undergraduate research: distributions, tests and effect sizes.',
      details: 'Explains descriptive stats, the logic of hypothesis testing, choosing between t-test/chi-square/ANOVA, what p-values do and don\'t mean, and why you should report effect sizes and confidence intervals alongside accuracy numbers.',
      learnPoints: ['Choose the right statistical test with a simple decision tree', 'Report results in the format journals expect', 'Explain p-values without the usual myths'],
      url: null,
      tags: ['Statistics', 'Analysis', 'Methods']
    },
    {
      id: 12,
      title: 'SPSS & R Basics for Students',
      category: 'Statistics',
      type: 'Guide',
      typeIcon: 'fa-book-open',
      level: 'Beginner',
      minutes: 15,
      description: 'Run your first descriptive statistics and t-test in SPSS or R with step-by-step screenshots.',
      details: 'A hands-on walkthrough: importing survey data, cleaning columns, computing descriptive statistics, running an independent t-test and reading the output table. Includes the same workflow twice — once in SPSS menus, once in five lines of R.',
      learnPoints: ['Import and clean survey data confidently', 'Run and interpret a t-test in SPSS or R', 'Export publication-ready tables'],
      url: null,
      tags: ['SPSS', 'R', 'Statistics', 'Tutorial']
    },
    {
      id: 13,
      title: 'Kaggle Datasets',
      category: 'Dataset',
      typeIcon: 'fa-database',
      type: 'Dataset',
      level: 'All',
      minutes: 5,
      description: 'Thousands of public datasets plus free notebooks — the fastest place to find data for ML projects.',
      details: 'Search by domain, filter by size and license, and fork a notebook that already loads the dataset. Also covers how to cite a Kaggle dataset properly in IEEE style.',
      learnPoints: ['Find licensed datasets for almost any ML topic', 'Start from existing notebooks to save weeks', 'Cite datasets correctly'],
      url: 'https://www.kaggle.com/datasets',
      tags: ['Dataset', 'Kaggle', 'Machine learning']
    },
    {
      id: 14,
      title: 'UCI Machine Learning Repository',
      category: 'Dataset',
      typeIcon: 'fa-database',
      type: 'Dataset',
      level: 'All',
      minutes: 4,
      description: 'The classic curated dataset archive — clean, documented, and citation-ready for coursework.',
      details: 'Hundreds of small-to-medium classic datasets (iris, heart disease, intrusion detection) with consistent documentation. Ideal when you need a benchmark dataset that reviewers already know.',
      learnPoints: ['Pick standard benchmark datasets reviewers trust', 'Understand dataset documentation conventions', 'Compare fairly against published baselines'],
      url: 'https://archive.ics.uci.edu/',
      tags: ['Dataset', 'Benchmark', 'UCI']
    },
    {
      id: 15,
      title: 'Google Dataset Search',
      category: 'Dataset',
      typeIcon: 'fa-database',
      type: 'Tool',
      level: 'All',
      minutes: 3,
      description: 'A search engine dedicated to datasets across repositories, governments and journals.',
      details: 'Like Google Scholar but for data: filter by usage license, update date and download format. Especially useful for finding government open-data portals and journal-published supplementary data.',
      learnPoints: ['Search datasets by topic and license', 'Discover government and journal data portals', 'Check licensing before using a dataset'],
      url: 'https://datasetsearch.research.google.com/',
      tags: ['Dataset', 'Search', 'Open data']
    },
    {
      id: 16,
      title: 'Overleaf: LaTeX for Papers',
      category: 'Research Tools',
      typeIcon: 'fa-screwdriver-wrench',
      type: 'Tool',
      level: 'Intermediate',
      minutes: 10,
      description: 'Write journal papers in LaTeX with no local setup, using IEEE and ACM templates.',
      details: 'Overleaf runs in the browser, collaborates in real time and ships official IEEE/ACM/Springer templates. This guide covers the first 30 minutes: picking a template, compiling, adding figures and fighting common errors.',
      learnPoints: ['Start an IEEE template in under 5 minutes', 'Add figures, tables and equations correctly', 'Collaborate with your supervisor in real time'],
      url: 'https://www.overleaf.com/',
      tags: ['LaTeX', 'Overleaf', 'Writing', 'Tool']
    },
    {
      id: 17,
      title: 'Google Scholar Alerts for Your Topic',
      category: 'Research Tools',
      typeIcon: 'fa-screwdriver-wrench',
      type: 'Guide',
      level: 'Beginner',
      minutes: 5,
      description: 'Set up keyword alerts so new papers in your area arrive in your inbox automatically.',
      details: 'Shows how to craft alert queries (with quotes and minus operators), how many alerts to run, and a weekly 15-minute routine to triage results into your literature matrix.',
      learnPoints: ['Create effective Scholar alert queries', 'Triage new papers in 15 minutes a week', 'Track citations of your key papers'],
      url: 'https://scholar.google.com/',
      tags: ['Google Scholar', 'Alerts', 'Literature review']
    },
    {
      id: 18,
      title: 'Using AI Tools Responsibly in Research',
      category: 'AI for Research',
      typeIcon: 'fa-robot',
      type: 'Guide',
      level: 'Intermediate',
      minutes: 13,
      description: 'Where AI assistance is legitimate (searching, summarizing, polishing) and where it is misconduct.',
      details: 'A practical policy guide: acceptable uses (literature discovery, grammar polishing, code explanation), grey zones (paraphrasing others\' text), and prohibited uses (generating results, fake citations, ghost-writing). Includes a disclosure statement template many journals now require.',
      learnPoints: ['Separate legitimate AI assistance from misconduct', 'Verify every AI-generated citation manually', 'Write the AI-use disclosure journals ask for'],
      url: null,
      tags: ['AI ethics', 'Research integrity', 'ChatGPT']
    },
    {
      id: 19,
      title: 'AI-Assisted Literature Surveys',
      category: 'AI for Research',
      typeIcon: 'fa-robot',
      type: 'Guide',
      level: 'Intermediate',
      minutes: 12,
      description: 'Use tools like Elicit and Semantic Scholar to map a field in days instead of months — then verify everything.',
      details: 'A workflow that pairs AI research assistants with traditional databases: seed papers → AI-suggested related work → snowball search → verification pass. Emphasizes that AI suggestions are a starting map, never a final bibliography.',
      learnPoints: ['Map an unfamiliar field with AI-assisted discovery', 'Snowball from key papers systematically', 'Verify every AI suggestion before citing'],
      url: null,
      tags: ['AI', 'Literature review', 'Elicit', 'Semantic Scholar']
    },
    {
      id: 20,
      title: 'Turnitin & Plagiarism Self-Checks',
      category: 'Academic Writing',
      typeIcon: 'fa-copy',
      type: 'Guide',
      level: 'Beginner',
      minutes: 8,
      description: 'Understand similarity scores, run safe self-checks and fix problems before your supervisor does.',
      details: 'Explains what a similarity score actually measures, why quoted text and references inflate it, how to use your university Turnitin allowance wisely, and paraphrasing techniques that show understanding rather than disguise copying.',
      learnPoints: ['Interpret similarity reports correctly', 'Self-check without burning your official attempt', 'Paraphrase properly instead of patchwriting'],
      url: null,
      tags: ['Plagiarism', 'Turnitin', 'Integrity']
    }
  ];

  /* --------------------------- Publication guides ------------------------ */

  const publicationGuides = [
    {
      id: 'journal-selection',
      icon: 'fa-book-open',
      title: 'Journal Selection',
      summary: 'How to pick a journal that matches your paper\'s scope, quality and timeline — and avoid predatory traps.',
      sections: [
        { heading: 'Match scope before prestige', body: 'Read the journal\'s aims & scope page and its last two issues. If your topic or methods never appear there, a desk rejection is almost guaranteed regardless of quality.' },
        { heading: 'Check legitimacy signals', body: 'Legitimate journals are indexed (Scopus, Web of Science, DOAJ), list real editorial boards with affiliations, and have a verifiable publisher website. Predatory journals chase you first with guaranteed-fast acceptance emails.' },
        { heading: 'Balance cost and speed', body: 'Compare APC (article processing charges), average review time (often published on the journal site or in review-time databases) and acceptance rate. For a first undergraduate paper, a solid national conference or a DOAJ-indexed journal is often the fastest credible route.' }
      ],
      tips: [
        'Check if your target journal published a paper citing your method — that\'s a good scope signal.',
        'Search the editor names + "predatory" before submitting anywhere unfamiliar.',
        'Ask your supervisor which journals they publish in; co-authorship smooths the path.',
        'Keep a shortlist of three journals ranked A/B/C before you format anything.'
      ]
    },
    {
      id: 'paper-formatting',
      icon: 'fa-file-lines',
      title: 'Paper Formatting',
      summary: 'Turn your thesis chapter into a journal-length paper using the official template from day one.',
      sections: [
        { heading: 'Write in the template, not before', body: 'Download the journal\'s LaTeX or Word template immediately and write directly into its two-column layout. Papers written "free-form first" always need painful cutting later.' },
        { heading: 'Restructure: thesis ≠ paper', body: 'A thesis chapter explains everything; a paper argues one contribution. Collapse your literature review to what positions the gap, move methodology details to a repository, and lead the abstract with the result.' },
        { heading: 'Figures and tables to spec', body: 'Rebuild figures at final column width with readable font sizes (≥8pt), consistent colour scheme, and captions that stand alone. Screenshots of thesis-resolution figures are the most common format complaint.' }
      ],
      tips: [
        'Most CS venues: 6–8 pages. Count early, cut early.',
        'Name figure files fig1.pdf, fig2.pdf and reference them by \\\\ref — never hardcode numbers.',
        'Run the template\'s spell-check in the journal\'s English variant (US/UK) consistently.',
        'Generate the bibliography with BibTeX/Zotero, never by hand.'
      ]
    },
    {
      id: 'citation-referencing',
      icon: 'fa-quote-right',
      title: 'Citation & Referencing',
      summary: 'Master the citation style your target venue uses and manage hundreds of references without losing any.',
      sections: [
        { heading: 'One style, applied perfectly', body: 'Identify the required style (IEEE for most engineering venues, APA for social science) and follow its official guide — not examples from other papers, which often contain inherited errors.' },
        { heading: 'Automate with a reference manager', body: 'Zotero or Mendeley stores every source once and formats it in any style on demand. Export BibTeX for LaTeX, or use the Word plugin for inline citations. Manual renumbering after every revision is wasted hours.' },
        { heading: 'Cite with intent', body: 'Every citation has a job: supporting a claim, crediting a method, or positioning a gap. If you can\'t say what job a citation does, either the sentence or the citation should go.' }
      ],
      tips: [
        'Cite datasets and software tools too — venues increasingly require it.',
        'Never cite a paper you haven\'t at least skimmed; AI-suggested citations must be verified.',
        'Check every DOI resolves before submission.',
        'Keep page numbers for direct quotes; check whether your style requires them.'
      ]
    },
    {
      id: 'plagiarism-awareness',
      icon: 'fa-copy',
      title: 'Plagiarism Awareness',
      summary: 'What counts as plagiarism beyond copy-paste, how similarity checkers work, and how to stay safely original.',
      sections: [
        { heading: 'Plagiarism is more than copying', body: 'Reusing structure with new words (patchwriting), uncited paraphrase, self-plagiarism across your own submissions, and uncredited figures or code all count. Checkers catch some of these; human reviewers catch the rest.' },
        { heading: 'Understand the similarity score', body: 'A 20% similarity report is not automatically guilty: quotes, references and standard method descriptions inflate it. What matters is matched passages in your results and argument sections.' },
        { heading: 'Original by construction', body: 'Take notes in your own words with the source closed, cite as you write (not afterwards), and use similarity reports diagnostically — treat a high match as a list of paragraphs to rewrite properly.' }
      ],
      tips: [
        'Run a draft through your university Turnitin allowance before final submission.',
        'Paraphrase tests: could you explain the idea aloud without the paper? Then write that.',
        'Declare AI assistance if the venue requires it — hidden use is treated as misconduct.',
        'Keep your notes and drafts; they are your evidence of original work.'
      ]
    },
    {
      id: 'peer-review',
      icon: 'fa-user-check',
      title: 'Peer Review',
      summary: 'What happens after you press submit, how reviewers think, and how to respond to criticism professionally.',
      sections: [
        { heading: 'The review lifecycle', body: 'Editor desk-check → reviewers assigned (2–4) → reports → editor decision (accept / minor / major / reject). Engineering venues average two to six months for the first decision; conference deadlines are fixed instead.' },
        { heading: 'How reviewers read', body: 'Reviewers typically spend one focused pass: abstract, figures, results, then the whole paper. Weak abstracts and unreadable figures create negative momentum that methodological excellence rarely reverses.' },
        { heading: 'Respond like a professional', body: 'Address every comment point-by-point, quote what you changed and where, thank reviewers for catches, and argue respectfully where you disagree with evidence. Rebuttals win major-revision decisions more than new experiments do.' }
      ],
      tips: [
        'Expect "major revision" — it is a normal first outcome, not a failure.',
        'Write the response letter as a table: comment | response | change location.',
        'Never argue tone; answer substance.',
        'Resubmit before the deadline the editor gives you.'
      ]
    },
    {
      id: 'journal-submission',
      icon: 'fa-paper-plane',
      title: 'Journal Submission',
      summary: 'The practical mechanics of submitting: cover letters, metadata, suggest-reviewers and tracking.',
      sections: [
        { heading: 'Prepare the submission package', body: 'Most portals want: the manuscript (sometimes anonymized), highlights or graphical abstract, cover letter, author contributions, and conflict-of-interest statements. Prepare these before creating the portal account to avoid timeout issues.' },
        { heading: 'Write a real cover letter', body: 'Three short paragraphs: what the paper does, why it fits this journal specifically, and confirmation that the work is original and not under review elsewhere. Editors skim this first — make the fit argument explicit.' },
        { heading: 'Metadata matters', body: 'Keywords drive reviewer matching. Suggest reviewers who cite your area but are not your co-authors or colleagues; oppose reviewers only with concrete conflict evidence, not disagreement.' }
      ],
      tips: [
        'Use institutional emails for all authors — flagged otherwise.',
        'Agree author order and contributions in writing before submission.',
        'Save the submission ID and set a calendar reminder for the editor\'s decision window.',
        'Never double-submit the same paper to two venues.'
      ]
    },
    {
      id: 'publication-ethics',
      icon: 'fa-scale-balanced',
      title: 'Publication Ethics',
      summary: 'Authorship rules, conflicts of interest, data integrity and the boundaries of AI assistance.',
      sections: [
        { heading: 'Who is an author?', body: 'Authorship requires substantive intellectual contribution plus accountability for the work. Order reflects contribution, decided early and openly. "Gift" authorship (adding a name for funding or courtesy) and ghost authorship are both misconduct.' },
        { heading: 'Integrity of data and images', body: 'Report what you did, including failed runs; do not crop, splice or enhance images to hide inconvenient results. Publish code and data where possible — reproducibility is your best protection against accusations.' },
        { heading: 'AI assistance boundaries', body: 'Current consensus: AI tools may assist with language and literature discovery but cannot be an author, and their output must be verified and disclosed per venue policy. Fabricating results or citations with AI is research fraud.' }
      ],
      tips: [
        'Discuss authorship with your supervisor at project start, not at submission.',
        'Follow COPE guidelines (cope.org) as the reference for edge cases.',
        'Declare all funding and conflicts even when it feels unnecessary.',
        'If you spot an error after publication, tell the editor — corrections are respected, concealment is not.'
      ]
    }
  ];

  /* ------------------------------ Roadmap steps -------------------------- */

  const roadmapSteps = [
    {
      id: 1,
      icon: 'fa-compass',
      title: 'Choose Research Area',
      explanation: 'Pick the broad field you want to work in for the next year. The right area sits at the intersection of your curiosity, your skill floor and your supervisor availability.',
      actions: [
        'Browse the Research Ideas explorer and shortlist 3 categories that excite you',
        'Check which areas your department\'s supervisors actually cover',
        'Discuss your shortlist with a senior student or academic advisor'
      ],
      resources: [
        { label: 'Research Methodology 101 (Resources)', url: 'resources.html' },
        { label: 'Explore Research Ideas', url: 'research.html' }
      ]
    },
    {
      id: 2,
      icon: 'fa-magnifying-glass',
      title: 'Find Research Gap',
      explanation: 'Within your area, find what is missing: a question nobody answered, a method untested in your context, or a contradiction between two papers.',
      actions: [
        'Read 5 recent survey papers in your area and note their "open problems" sections',
        'Fill a synthesis matrix for the 10 most-cited papers',
        'Write one sentence: "It is known that X, but Y is unknown because Z"'
      ],
      resources: [
        { label: 'Finding Your Research Gap (Resources)', url: 'resources.html' },
        { label: 'Google Scholar', url: 'https://scholar.google.com/' }
      ]
    },
    {
      id: 3,
      icon: 'fa-bullseye',
      title: 'Select Topic',
      explanation: 'Convert the gap into a specific, finishable topic with a measurable outcome and a fallback plan.',
      actions: [
        'Write your title as a question that can be answered with evidence',
        'Define what "done" looks like: dataset, accuracy target, working prototype',
        'Prepare a smaller fallback scope in case experiments underdeliver'
      ],
      resources: [
        { label: 'Browse 500+ idea cards for inspiration', url: 'research.html' },
        { label: 'Literature Review Starter Kit (Resources)', url: 'resources.html' }
      ]
    },
    {
      id: 4,
      icon: 'fa-user-tie',
      title: 'Find Supervisor',
      explanation: 'Match your topic to a supervisor whose expertise covers your methods, then convince them with preparation, not enthusiasm alone.',
      actions: [
        'Use the supervisor matching tool to shortlist 3 faculty members',
        'Read two of each candidate\'s recent papers before emailing them',
        'Send a one-page proposal: gap, question, plan, timeline'
      ],
      resources: [
        { label: 'Supervisor Matching tool', url: 'supervisors.html' },
        { label: 'How to Read a Research Paper (Resources)', url: 'resources.html' }
      ]
    },
    {
      id: 5,
      icon: 'fa-flask',
      title: 'Conduct Research',
      explanation: 'Execute your methodology in small, verifiable increments. Keep a lab notebook and version-control everything from day one.',
      actions: [
        'Set up Git + a documented experiment log before the first experiment',
        'Reproduce one published baseline before building anything new',
        'Meet your supervisor on a fixed schedule with visible progress each time'
      ],
      resources: [
        { label: 'Kaggle Datasets', url: 'https://www.kaggle.com/datasets' },
        { label: 'Statistics for Research (Resources)', url: 'resources.html' }
      ]
    },
    {
      id: 6,
      icon: 'fa-pen-nib',
      title: 'Write Thesis',
      explanation: 'Write continuously during the research, not after it. Chapters drafted alongside experiments are twice as accurate and half as painful.',
      actions: [
        'Draft methodology and literature chapters while experiments run',
        'Follow your department\'s formatting template from the first page',
        'Get chapter feedback in small batches instead of one final dump'
      ],
      resources: [
        { label: 'Thesis Writing Survival Guide (Resources)', url: 'resources.html' },
        { label: 'Academic Writing Structure (Resources)', url: 'resources.html' }
      ]
    },
    {
      id: 7,
      icon: 'fa-file-lines',
      title: 'Convert Thesis to Paper',
      explanation: 'A paper is not a short thesis: it is one contribution, argued tightly, written directly in the venue\'s template.',
      actions: [
        'Choose the single strongest contribution and build the paper around it',
        'Write in the target journal/conference template from day one',
        'Ask your supervisor about co-authorship and author order now'
      ],
      resources: [
        { label: 'Paper Formatting guide (Publication Hub)', url: 'publication.html' },
        { label: 'Overleaf templates', url: 'https://www.overleaf.com/' }
      ]
    },
    {
      id: 8,
      icon: 'fa-paper-plane',
      title: 'Submit to Journal',
      explanation: 'Prepare the full submission package, verify the venue is legitimate, submit, and track the decision professionally.',
      actions: [
        'Run the journal submission checklist below before submitting',
        'Write a cover letter that argues scope fit explicitly',
        'Calendar the expected decision date and prepare for "major revision"'
      ],
      resources: [
        { label: 'Journal Selection guide (Publication Hub)', url: 'publication.html' },
        { label: 'COPE ethics guidelines', url: 'https://publicationethics.org/' }
      ]
    }
  ];

  /* --------------------------------- FAQ --------------------------------- */

  const faqs = [
    {
      q: 'What is ThesisBridge BD?',
      a: 'ThesisBridge BD is a centralized digital hub where Bangladeshi undergraduate students can discover thesis and project ideas, find suitable supervisors, learn research methodology and understand how journal publication works — all in one place, from first idea to final submission.'
    },
    {
      q: 'Who can use it?',
      a: 'It is designed primarily for undergraduate students in computer science, engineering and related disciplines at Bangladeshi universities. Graduate students, supervisors and faculty can also use it to explore research directions and share structured guidance.'
    },
    {
      q: 'How can I find thesis ideas?',
      a: 'Open the Research Ideas explorer, then search by keyword or combine filters — category (AI, IoT, cybersecurity and more), difficulty, research type and technology. Every idea card shows the problem, research gap, suggested methodology and expected outcome, and you can bookmark ideas to your Saved panel.'
    },
    {
      q: 'How does supervisor matching work?',
      a: 'You answer four questions — research area, technologies you know, preferred research type and preferred difficulty. A simple scoring algorithm compares your answers with each supervisor\'s areas and expertise and shows a match percentage. It is clearly a demo: a frontend prototype to help you shortlist faculty, not an official academic recommendation.'
    },
    {
      q: 'Can I find research gaps?',
      a: 'Yes. Each research idea includes an explicit research gap, and the Resources library includes a dedicated guide and worksheet for mining gaps from limitations sections, "future work" paragraphs and unexplored local contexts.'
    },
    {
      q: 'How do I convert a thesis into a paper?',
      a: 'The Publication Hub\'s Paper Formatting guide walks through it: pick one contribution, restructure your thesis chapter into a 6–8 page argument, write directly in the venue template, and shrink the literature review to only what positions your gap.'
    },
    {
      q: 'How do I choose a journal?',
      a: 'Start with the Journal Selection guide in the Publication Hub: match the journal\'s scope to your topic, verify it is indexed (Scopus, DOAJ) rather than predatory, and balance publication cost against review time. Keeping a ranked shortlist of three venues before formatting saves weeks.'
    },
    {
      q: 'Is the platform free?',
      a: 'Yes — browsing ideas, supervisor profiles, guides, checklists and resources is completely free. Creating an account lets you save ideas and track progress, and those lists are stored in our Supabase database so they follow you to any device.'
    }
  ];

  /* ---------------------------- Journal checklist ------------------------ */

  const journalChecklist = [
    { id: 'q1', label: 'Research question finalized' },
    { id: 'q2', label: 'Literature review completed' },
    { id: 'q3', label: 'Methodology documented' },
    { id: 'q4', label: 'Results analyzed' },
    { id: 'q5', label: 'References formatted' },
    { id: 'q6', label: 'Journal selected' },
    { id: 'q7', label: 'Manuscript formatted' },
    { id: 'q8', label: 'Submission requirements checked' }
  ];

  return {
    categories, difficulties, types, technologies, quizTechnologies,
    universities, departments, expertiseOptions,
    researchIdeas, supervisors, resources, publicationGuides,
    roadmapSteps, faqs, journalChecklist
  };
})();
