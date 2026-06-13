"""
HalAudit Seed Data
Pre-built corpus of factual paragraphs covering science, geography, history,
and technology to ensure the demo works out of the box.
"""

SEED_CORPUS = [
    # ====================== SCIENCE: PHYSICS ======================
    {
        "text": "The speed of light in a vacuum is approximately 299,792,458 meters per second. This is a fundamental constant of nature denoted by the letter c. Nothing with mass can travel at or faster than the speed of light.",
        "source": "Physics - Speed of Light"
    },
    {
        "text": "Albert Einstein published his special theory of relativity in 1905 and his general theory of relativity in 1915. The famous equation E=mc² relates energy and mass. Einstein was awarded the Nobel Prize in Physics in 1921 for his discovery of the photoelectric effect, not for relativity.",
        "source": "Physics - Einstein & Relativity"
    },
    {
        "text": "Isaac Newton formulated the laws of motion and universal gravitation. His work 'Philosophiæ Naturalis Principia Mathematica' was published in 1687. Newton's three laws of motion form the foundation of classical mechanics.",
        "source": "Physics - Newton's Laws"
    },
    {
        "text": "Gravity is the weakest of the four fundamental forces of nature. The four fundamental forces are: gravitational, electromagnetic, strong nuclear, and weak nuclear. The strong nuclear force is the strongest of the four.",
        "source": "Physics - Fundamental Forces"
    },
    {
        "text": "The Higgs boson was discovered at CERN's Large Hadron Collider in 2012. Peter Higgs and François Englert won the Nobel Prize in Physics in 2013 for theoretically predicting its existence. The Higgs boson gives other particles their mass through the Higgs field.",
        "source": "Physics - Higgs Boson"
    },
    {
        "text": "Quantum mechanics describes the behavior of particles at the atomic and subatomic level. The Heisenberg uncertainty principle states that it is impossible to simultaneously know both the exact position and exact momentum of a particle. Schrödinger's equation describes how quantum states evolve over time.",
        "source": "Physics - Quantum Mechanics"
    },

    # ====================== SCIENCE: BIOLOGY ======================
    {
        "text": "DNA stands for deoxyribonucleic acid. The structure of DNA was first described by James Watson and Francis Crick in 1953, based on X-ray crystallography data from Rosalind Franklin. DNA has a double helix structure with four nucleotide bases: adenine (A), thymine (T), guanine (G), and cytosine (C).",
        "source": "Biology - DNA Structure"
    },
    {
        "text": "The human body contains approximately 37.2 trillion cells. Red blood cells carry oxygen through the body using hemoglobin. White blood cells are part of the immune system. Platelets help with blood clotting.",
        "source": "Biology - Human Cells"
    },
    {
        "text": "Charles Darwin published 'On the Origin of Species' in 1859. His theory of evolution by natural selection explains how species change over time through the survival and reproduction of individuals best adapted to their environment. Darwin traveled on HMS Beagle, not HMS Discovery.",
        "source": "Biology - Evolution"
    },
    {
        "text": "Photosynthesis is the process by which plants convert sunlight, water, and carbon dioxide into glucose and oxygen. The chemical equation is 6CO₂ + 6H₂O + light energy → C₆H₁₂O₆ + 6O₂. Chlorophyll is the pigment that absorbs sunlight, primarily in the blue and red wavelengths.",
        "source": "Biology - Photosynthesis"
    },
    {
        "text": "The human genome contains approximately 20,000 to 25,000 protein-coding genes. The Human Genome Project was completed in 2003. Humans share approximately 98.7% of their DNA with chimpanzees.",
        "source": "Biology - Human Genome"
    },
    {
        "text": "Mitochondria are known as the powerhouse of the cell. They generate most of the cell's supply of adenosine triphosphate (ATP), which is used as a source of chemical energy. Mitochondria have their own DNA, separate from the cell's nuclear DNA.",
        "source": "Biology - Mitochondria"
    },

    # ====================== SCIENCE: CHEMISTRY ======================
    {
        "text": "Water has the chemical formula H₂O. It boils at 100 degrees Celsius (212 degrees Fahrenheit) at standard atmospheric pressure and freezes at 0 degrees Celsius (32 degrees Fahrenheit). Water is one of the few substances that expands when it freezes.",
        "source": "Chemistry - Water Properties"
    },
    {
        "text": "The periodic table was first published by Dmitri Mendeleev in 1869. It currently contains 118 confirmed elements. The lightest element is hydrogen with atomic number 1, and the heaviest naturally occurring element is uranium with atomic number 92.",
        "source": "Chemistry - Periodic Table"
    },
    {
        "text": "Gold has the chemical symbol Au, derived from the Latin word 'aurum'. Its atomic number is 79. Gold is one of the least reactive chemical elements, which is why it doesn't tarnish or corrode. Gold is a very good conductor of electricity.",
        "source": "Chemistry - Gold"
    },
    {
        "text": "Oxygen makes up approximately 21% of Earth's atmosphere by volume. Nitrogen makes up approximately 78%. Argon constitutes about 0.93%, and carbon dioxide about 0.04%. The atmosphere extends to about 10,000 km above Earth's surface.",
        "source": "Chemistry - Atmosphere Composition"
    },

    # ====================== GEOGRAPHY ======================
    {
        "text": "The Earth has seven continents: Africa, Antarctica, Asia, Australia (Oceania), Europe, North America, and South America. Asia is the largest continent by both area and population. Antarctica is the least populated continent.",
        "source": "Geography - Continents"
    },
    {
        "text": "Mount Everest is the tallest mountain above sea level, standing at 8,849 meters (29,032 feet). It is located on the border between Nepal and Tibet (China) in the Himalayas. The first confirmed ascent was by Edmund Hillary and Tenzing Norgay on May 29, 1953.",
        "source": "Geography - Mount Everest"
    },
    {
        "text": "The Pacific Ocean is the largest and deepest ocean on Earth, covering approximately 165.25 million square kilometers. The Mariana Trench, located in the western Pacific Ocean, is the deepest known oceanic trench, reaching a depth of about 10,994 meters at the Challenger Deep.",
        "source": "Geography - Pacific Ocean"
    },
    {
        "text": "The Amazon River is the largest river in the world by discharge volume of water. However, the Nile River is generally considered the longest river at approximately 6,650 km, though some measurements put the Amazon at a similar or greater length. The Amazon flows through South America.",
        "source": "Geography - Rivers"
    },
    {
        "text": "The Sahara Desert is the largest hot desert in the world, covering approximately 9.2 million square kilometers in North Africa. However, Antarctica is technically the largest desert overall due to its extremely low precipitation levels.",
        "source": "Geography - Deserts"
    },
    {
        "text": "Russia is the largest country in the world by area, spanning approximately 17.1 million square kilometers. It spans 11 time zones. Canada is the second-largest country by total area. China and the United States follow as the third and fourth largest.",
        "source": "Geography - Countries by Area"
    },
    {
        "text": "Tokyo is the capital of Japan. Beijing is the capital of China. New Delhi is the capital of India. Canberra, not Sydney, is the capital of Australia. Brasilia, not Rio de Janeiro, is the capital of Brazil. Ottawa, not Toronto, is the capital of Canada.",
        "source": "Geography - World Capitals"
    },
    {
        "text": "The Great Wall of China is not visible from space with the naked eye under normal conditions. This is a common misconception. The wall is only about 5-8 meters wide, which is too narrow to be distinguished from orbit without aid.",
        "source": "Geography - Great Wall of China"
    },

    # ====================== HISTORY ======================
    {
        "text": "World War I lasted from 1914 to 1918. It was triggered by the assassination of Archduke Franz Ferdinand of Austria-Hungary in Sarajevo on June 28, 1914. The war ended with the armistice on November 11, 1918. The Treaty of Versailles was signed on June 28, 1919.",
        "source": "History - World War I"
    },
    {
        "text": "World War II lasted from 1939 to 1945. It began with Nazi Germany's invasion of Poland on September 1, 1939. The war in Europe ended on May 8, 1945 (V-E Day). Japan surrendered on August 15, 1945 (V-J Day), following the atomic bombings of Hiroshima on August 6 and Nagasaki on August 9, 1945.",
        "source": "History - World War II"
    },
    {
        "text": "The Declaration of Independence of the United States was adopted on July 4, 1776. Thomas Jefferson was the principal author. It declared the thirteen American colonies independent from Great Britain. George Washington was the first president of the United States, inaugurated in 1789.",
        "source": "History - American Independence"
    },
    {
        "text": "The French Revolution began in 1789 with the storming of the Bastille on July 14, 1789. The revolution led to the end of the monarchy and the execution of King Louis XVI in 1793. Napoleon Bonaparte rose to power afterward, crowning himself Emperor in 1804.",
        "source": "History - French Revolution"
    },
    {
        "text": "The Roman Empire was founded in 27 BC when Augustus became the first Roman Emperor. The Western Roman Empire fell in 476 AD. At its height, the Roman Empire controlled territory spanning from Britain to Egypt and from Spain to Mesopotamia.",
        "source": "History - Roman Empire"
    },
    {
        "text": "The Renaissance was a cultural movement that began in Italy in the 14th century and spread across Europe. Key figures include Leonardo da Vinci, Michelangelo, and Raphael. The printing press was invented by Johannes Gutenberg around 1440, revolutionizing the spread of knowledge.",
        "source": "History - Renaissance"
    },
    {
        "text": "The Moon landing occurred on July 20, 1969, during the Apollo 11 mission. Neil Armstrong was the first person to walk on the Moon, followed by Buzz Aldrin. Michael Collins remained in lunar orbit. Armstrong's famous words were 'That's one small step for man, one giant leap for mankind.'",
        "source": "History - Moon Landing"
    },
    {
        "text": "The Berlin Wall was built in 1961 and fell on November 9, 1989. It divided East and West Berlin during the Cold War. Germany was officially reunified on October 3, 1990. The Cold War ended with the dissolution of the Soviet Union on December 26, 1991.",
        "source": "History - Berlin Wall"
    },

    # ====================== TECHNOLOGY ======================
    {
        "text": "The World Wide Web was invented by Tim Berners-Lee in 1989 while working at CERN. The first website went live on August 6, 1991. Berners-Lee created HTTP, HTML, and the first web browser. The internet itself predates the web and originated from ARPANET in the late 1960s.",
        "source": "Technology - World Wide Web"
    },
    {
        "text": "Apple Inc. was founded by Steve Jobs, Steve Wozniak, and Ronald Wayne on April 1, 1976, in Cupertino, California. The first iPhone was released on June 29, 2007. Steve Jobs passed away on October 5, 2011.",
        "source": "Technology - Apple Inc."
    },
    {
        "text": "Python is a high-level programming language created by Guido van Rossum and first released in 1991. JavaScript was created by Brendan Eich at Netscape and was first released in 1995. Java was developed by James Gosling at Sun Microsystems and released in 1995.",
        "source": "Technology - Programming Languages"
    },
    {
        "text": "Moore's Law, formulated by Gordon Moore in 1965, predicted that the number of transistors on integrated circuits would double approximately every two years. Modern processors contain billions of transistors. The first commercial microprocessor was the Intel 4004, released in 1971.",
        "source": "Technology - Moore's Law"
    },
    {
        "text": "Machine learning is a subset of artificial intelligence that enables computers to learn from data without being explicitly programmed. Deep learning is a subset of machine learning using artificial neural networks with many layers. GPT (Generative Pre-trained Transformer) models were developed by OpenAI.",
        "source": "Technology - AI & ML"
    },
    {
        "text": "The Linux kernel was created by Linus Torvalds in 1991. Linux is an open-source operating system. Android, the most widely used mobile operating system, is based on the Linux kernel. Linux powers the majority of web servers worldwide.",
        "source": "Technology - Linux"
    },
    {
        "text": "Bitcoin was invented in 2008 by an anonymous person or group using the pseudonym Satoshi Nakamoto. The Bitcoin whitepaper was published on October 31, 2008. The first Bitcoin transaction occurred on January 3, 2009. Blockchain is the underlying technology of Bitcoin.",
        "source": "Technology - Bitcoin"
    },

    # ====================== MATHEMATICS ======================
    {
        "text": "Pi (π) is an irrational number approximately equal to 3.14159. It represents the ratio of a circle's circumference to its diameter. Pi has been calculated to over 100 trillion digits. The concept of pi has been known for nearly 4,000 years.",
        "source": "Mathematics - Pi"
    },
    {
        "text": "The Pythagorean theorem states that in a right triangle, the square of the hypotenuse equals the sum of the squares of the other two sides (a² + b² = c²). It is named after the ancient Greek mathematician Pythagoras, though it was known to Babylonian mathematicians before him.",
        "source": "Mathematics - Pythagorean Theorem"
    },
    {
        "text": "Zero was first used as a number by Indian mathematicians around the 5th century. The concept was later transmitted to the Islamic world and then to Europe. The Fibonacci sequence (0, 1, 1, 2, 3, 5, 8, 13, ...) was introduced to Western mathematics by Leonardo of Pisa in 1202.",
        "source": "Mathematics - Number History"
    },

    # ====================== ASTRONOMY ======================
    {
        "text": "The Sun is a G-type main-sequence star (G2V). It is approximately 4.6 billion years old. The Sun accounts for about 99.86% of the total mass of the Solar System. Light from the Sun takes approximately 8 minutes and 20 seconds to reach Earth.",
        "source": "Astronomy - The Sun"
    },
    {
        "text": "There are eight planets in our Solar System: Mercury, Venus, Earth, Mars, Jupiter, Saturn, Uranus, and Neptune. Pluto was reclassified as a dwarf planet by the International Astronomical Union in 2006. Jupiter is the largest planet in the Solar System.",
        "source": "Astronomy - Solar System"
    },
    {
        "text": "The Milky Way galaxy contains an estimated 100 to 400 billion stars. It is a barred spiral galaxy approximately 100,000 light-years in diameter. The nearest star system to the Sun is Alpha Centauri, located approximately 4.37 light-years away.",
        "source": "Astronomy - Milky Way"
    },
    {
        "text": "A black hole is a region of spacetime where gravity is so strong that nothing, not even light, can escape. The first image of a black hole was captured by the Event Horizon Telescope in 2019, showing the black hole at the center of galaxy M87.",
        "source": "Astronomy - Black Holes"
    },

    # ====================== COMMON MISCONCEPTIONS ======================
    {
        "text": "Humans use all parts of their brains, not just 10%. The myth that we only use 10% of our brains is false. Different areas of the brain have specific functions, and brain imaging studies show activity across all regions during various tasks.",
        "source": "Misconceptions - Brain Usage"
    },
    {
        "text": "Goldfish have a memory span longer than 3 seconds. Studies have shown that goldfish can remember things for months. The idea that goldfish have a 3-second memory is a common myth.",
        "source": "Misconceptions - Goldfish Memory"
    },
    {
        "text": "Lightning can and does strike the same place twice. Tall buildings like the Empire State Building are struck by lightning dozens of times per year. The saying 'lightning never strikes twice' is a myth.",
        "source": "Misconceptions - Lightning"
    },
    {
        "text": "Bats are not blind. While many bat species use echolocation to navigate in the dark, all bat species have functional eyes. Some fruit bats have excellent vision. The phrase 'blind as a bat' is misleading.",
        "source": "Misconceptions - Bats Vision"
    },

    # ====================== ADDITIONAL FACTS ======================
    {
        "text": "The human heart beats approximately 100,000 times per day and about 35 million times per year. The adult human body contains approximately 5 liters of blood. Blood takes about 20 seconds to circulate through the entire body.",
        "source": "Medicine - Human Heart"
    },
    {
        "text": "The Great Barrier Reef is the world's largest coral reef system, stretching over 2,300 kilometers along the coast of Queensland, Australia. It is composed of over 2,900 individual reef systems and can be seen from space.",
        "source": "Nature - Great Barrier Reef"
    },
    {
        "text": "The speed of sound in air at sea level is approximately 343 meters per second or about 1,235 kilometers per hour. This is known as Mach 1. The speed of sound varies with temperature, humidity, and the medium through which it travels.",
        "source": "Physics - Speed of Sound"
    },
    {
        "text": "The Eiffel Tower was built for the 1889 World's Fair in Paris, France. It was designed by Gustave Eiffel's engineering company. The tower is 330 meters tall and was the tallest man-made structure in the world until the Chrysler Building was completed in New York in 1930.",
        "source": "Landmarks - Eiffel Tower"
    },
    {
        "text": "The Olympic Games originated in ancient Greece, with the first recorded games held in 776 BC in Olympia. The modern Olympic Games were founded by Pierre de Coubertin and began in Athens, Greece, in 1896. The Olympic rings represent the five inhabited continents.",
        "source": "Sports - Olympic Games"
    },
]


def get_seed_corpus():
    """Return the seed corpus as separate texts and metadata lists."""
    texts = [item["text"] for item in SEED_CORPUS]
    metadata = [{"source": item["source"]} for item in SEED_CORPUS]
    return texts, metadata
