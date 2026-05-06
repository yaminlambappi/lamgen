/**
 * Massive Procedural Data Pools for LamGen Mini Games
 * Organized by Game Engine
 */
window.GameData = {
    ranks: [
        { xp: 0, name: "Idle Human", color: "#8B7FFF" },
        { xp: 500, name: "Lab Survivor", color: "#3EECD8" },
        { xp: 1500, name: "Keyboard Warrior", color: "#F59E0B" },
        { xp: 3500, name: "Chaos Student", color: "#EF4444" },
        { xp: 7000, name: "Night Owl", color: "#8B5CF6" },
        { xp: 12000, name: "Brainrot Legend", color: "#EC4899" },
        { xp: 20000, name: "LamGen Architect", color: "#FCD34D" }
    ],
    
    typing: {
        categories: {
            coding: [
                "function initializeSystem(config) { return new Matrix(config); }",
                "git push origin master --force-with-lease",
                "const [state, setState] = useState(null);",
                "SELECT * FROM users WHERE sanity < 0;",
                "Uncaught TypeError: undefined is not a function",
                "while (true) { drinkCoffee(); writeCode(); }"
            ],
            genZ: [
                "No cap, this code is absolutely bussin.",
                "Bro really tried to center the div using margins 💀",
                "Rent free in my head fr fr.",
                "Main character energy right here.",
                "Caught in 4k debugging production."
            ],
            academic: [
                "In conclusion, the methodology proves inadequate.",
                "Despite the anomalous readings, the hypothesis holds.",
                "The socio-economic implications of this paradigm shift are vast.",
                "Please refer to Figure 4b for the statistical variance.",
                "Due at 11:59 PM, submitted at 11:58 PM."
            ],
            toxic: [
                "I could write a script to replace you.",
                "Are you typing with your elbows?",
                "My grandmother types faster, and she doesn't own a computer.",
                "Skill issue detected.",
                "Uninstall your keyboard."
            ]
        },
        absurdFragments: {
            subjects: ["A neon platypus", "The legendary hacker", "My sleep paralysis demon", "An over-caffeinated student"],
            actions: ["deleted the production database", "invented a new JavaScript framework", "started crying in binary", "tried to exit Vim"],
            endings: ["while eating a burrito.", "and then everything exploded.", "for no logical reason.", "because why not?"]
        }
    },

    wyr: {
        templates: [
            "Only communicate using {language}",
            "Never use {tech} again",
            "Have a permanent {ailment}",
            "Be instantly famous but {consequence}",
            "Live in a world without {concept}",
            "Every time you {action}, you {reaction}",
            "Fight one horse-sized {animal} or 100 duck-sized {animals}",
            "Have the ability to {superpower} but {drawback}",
            "Know exactly {knowledge}",
            "Have to wear {clothing} every day forever",
            "Only eat {food} for the rest of your life"
        ],
        components: {
            language: ["Python code", "obscure TikTok references", "Minecraft enchantment table language", "Gen-Z slang", "corporate jargon", "only emojis", "screams", "Morse code", "passive-aggressive emails"],
            tech: ["a computer", "smartphones", "the internet", "headphones", "Google", "StackOverflow", "Ctrl+C/Ctrl+V", "Wi-Fi", "microwaves"],
            ailment: ["500ms lag in real life", "itch you can never scratch", "pop-up ad in your vision", "low-battery anxiety", "buffering icon over your head", "dial-up sound in your ears", "feeling like you forgot your keys"],
            consequence: ["completely broke", "everyone hates you", "you can never leave your room", "you forget your own name", "you smell like garlic permanently", "you have to live in the woods"],
            concept: ["music", "memes", "coffee", "sleep", "indoor plumbing", "weekends", "Ctrl+Z", "the color blue"],
            action: ["sneeze", "laugh", "sleep", "code", "open your phone", "blink", "say 'hello'"],
            reaction: ["lose $1", "forget a random memory", "hear a Windows XP error sound", "teleport 1 inch to the left", "glow in the dark for 10 seconds", "honk like a goose"],
            animal: ["duck", "capybara", "pigeon", "goose", "crab", "raccoon", "hamster"],
            animals: ["horses", "lions", "bears", "elephants", "wolves", "cows", "kangaroos"],
            superpower: ["fly", "read minds", "turn invisible", "teleport", "stop time", "breathe underwater"],
            drawback: ["only at walking speed", "but you hear everyone's intrusive thoughts", "but you're blind when you do", "but you leave your clothes behind", "but you age 2x as fast", "only when no one is looking"],
            knowledge: ["when everyone dies", "how the universe ends", "what everyone truly thinks of you", "the winning lottery numbers but you can't play", "all the lore of Five Nights at Freddy's"],
            clothing: ["a damp swimsuit", "a clown suit", "heavy winter gear in summer", "a fedora", "shoes that are 1 size too small"],
            food: ["raw onions", "unseasoned chicken", "lukewarm tap water", "stale bread", "ghost peppers"]
        },
        modifiers: [
            " ...and nobody will ever know.",
            " ...but you get $10 million.",
            " ...for the rest of your life.",
            " ...but your best friend suffers the opposite.",
            " ...but you become immortal.",
            "",
            "",
            ""
        ]
    },

    roast: {
        templates: [
            "You have the {noun} of a {adj} {subject}.",
            "I'd explain {topic} to you, but I left my {resource} at home.",
            "Your {attribute} is basically a {tech_error}.",
            "You look like you struggle with {simple_task}.",
            "If {concept} was a sport, you'd win {metal}.",
            "You're the human equivalent of {annoying_thing}.",
            "I've seen {weak_thing} with more {positive_trait} than you.",
            "{person} called. They want their {bad_trait} back.",
            "You write {code_thing} like it's an apology letter to the compiler.",
            "Bro really thought {dumb_action} was a good idea 💀",
            "Your vibe screams '{absurd_vibe}'.",
            "You have the structural integrity of {weak_structure}."
        ],
        vocab: {
            noun: ["charisma", "intellect", "attention span", "aesthetic", "processing power", "survival instinct", "search history"],
            adj: ["broken", "laggy", "caffeinated", "depressed", "obsolete", "cursed", "overcooked", "malfunctioning", "abandoned"],
            subject: ["roomba", "dial-up modem", "potato", "404 page", "floppy disk", "Internet Explorer 6", "Discord mod", "unpaid intern", "wet napkin"],
            topic: ["basic logic", "common sense", "how to center a div", "social cues", "showering", "how to read"],
            resource: ["crayons", "patience", "time", "puppet theater", "flashcards"],
            attribute: ["personality", "codebase", "sense of humor", "academic record", "browser history", "dating life", "posture"],
            tech_error: ["syntax error", "memory leak", "blue screen of death", "merge conflict", "infinite loop", "NullPointerException", "segfault"],
            simple_task: ["revolving doors", "making toast", "reading an analog clock", "exiting Vim", "finding the power button", "typing your own name"],
            concept: ["laziness", "making bad decisions", "procrastination", "being confidently incorrect", "missing deadlines", "ignoring red flags"],
            metal: ["the participation trophy", "a plastic medal", "last place", "a cease and desist letter", "a restraining order"],
            annoying_thing: ["a YouTube unskippable ad", "a wet sock", "when the Wi-Fi drops 1 bar", "a Windows update mid-game", "paper straws", "a 4am fire alarm"],
            weak_thing: ["a wet paper towel", "Internet Explorer", "my grandma's WiFi", "a default password", "a chocolate teapot"],
            positive_trait: ["rizz", "logic", "processing power", "usefulness", "aesthetic appeal", "structural stability"],
            person: ["The year 2012", "Your compiler", "StackOverflow", "A middle schooler", "Your ex", "Gordon Ramsay"],
            bad_trait: ["cringe", "unresolved bugs", "lack of self-awareness", "spaghetti code", "terrible opinions"],
            code_thing: ["commits", "CSS", "Python scripts", "essays", "pull requests", "discussion board posts"],
            dumb_action: ["using light theme", "pushing to main", "replying 'all'", "buying an NFT", "investing in dogecoin at peak"],
            absurd_vibe: ["I ask questions during the syllabus reading", "I drink milk with ice", "I reply to automated emails", "I sleep in jeans"],
            weak_structure: ["Jenga tower played by toddlers", "a house of cards in a hurricane", "spaghetti code", "my mental health during finals week"]
        },
        comebacks: [
            { type: "savage", text: ["Still better than your existence.", "Did it take you all day to come up with that?", "I've heard better roasts from a compiled error log.", "I'd roast you back, but nature already did.", "You're proof that evolution can go in reverse."] },
            { type: "nerd", text: ["I'm rubber, you're glue; your IP is logged, I'm tracking you.", "At least my codebase compiles.", "O(1) effort roast right there.", "404 Roast Not Found.", "I've seen syntax errors that hurt my feelings more than this."] },
            { type: "brainrot", text: ["L + ratio + you fell off.", "Bro is projecting 💀", "Touch grass immediately.", "Skill issue tbh.", "Who let him cook? 🗑️"] }
        ]
    }
};
