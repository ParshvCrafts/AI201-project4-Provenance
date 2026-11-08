"""
What my test runs. (unit 8, Milestone 3)  `run_eval.py` runs everything here three times.

One scenario per criterion in criteria.md. Where each text comes from:

- Human texts are pre-2020 published prose, copied exactly from Project
  Gutenberg plain-text editions (book and year in the comment beside each).
  None of them is one of the six calibration texts in calibrate.py, so the
  test isn't scored on the same texts I tuned the anchors on.
- AI texts were generated with Claude for this test, in the generic
  explainer register a student would paste in.

A scenario carries either "texts" (sent with a made-up creator_id) or
"bodies" (sent exactly as written). Two extra keys are mine:

    "appeal": True       after each 200, run_eval.py appeals that content_id and
                         checks status, the appeal log entry, and that the
                         original decision entry is still there.
    "fake_appeals": N    also send N appeals against ids that were never issued.
"""

SCENARIOS = [
    {
        "name": "human writing",
        "criterion": 1,
        # Target: 0 of 10 get the AI label, in every trial.
        # Plain: Douglass, Baum, Franklin, London, Jerome. Formal: Thoreau, Austen, Melville.
        "texts": [
            # Douglass, Narrative of the Life of Frederick Douglass (1845)
            'The colonel, after ascertaining where the slave belonged, rode on; the man also went on about his business, not dreaming that he had been conversing with his master. He thought, said, and heard nothing more of the matter, until two or three weeks afterwards. The poor man was then informed by his overseer that, for having found fault with his master, he was now to be sold to a Georgia trader. He was immediately chained and handcuffed; and thus, without a moment’s warning, he was snatched away, and forever sundered, from his family and friends, by a hand more unrelenting than death. This is the penalty of telling the truth, of telling the simple truth, in answer to a series of plain questions.',
            # Baum, The Wonderful Wizard of Oz (1900)
            'They now came upon more and more of the big scarlet poppies, and fewer and fewer of the other flowers; and soon they found themselves in the midst of a great meadow of poppies. Now it is well known that when there are many of these flowers together their odor is so powerful that anyone who breathes it falls asleep, and if the sleeper is not carried away from the scent of the flowers, he sleeps on and on forever. But Dorothy did not know this, nor could she get away from the bright red flowers that were everywhere about; so presently her eyes grew heavy and she felt she must sit down to rest and to sleep.',
            # Thoreau, Walden (1854)
            'With a little more deliberation in the choice of their pursuits, all men would perhaps become essentially students and observers, for certainly their nature and destiny are interesting to all alike. In accumulating property for ourselves or our posterity, in founding a family or a state, or acquiring fame even, we are mortal; but in dealing with truth we are immortal, and need fear no change nor accident. The oldest Egyptian or Hindoo philosopher raised a corner of the veil from the statue of the divinity; and still the trembling robe remains raised, and I gaze upon as fresh a glory as he did, since it was I in him that was then so bold, and it is he in me that now reviews the vision. No dust has settled on that robe; no time has elapsed since that divinity was revealed. That time which we really improve, or which is improvable, is neither past, present, nor future.',
            # Austen, Pride and Prejudice (1813)
            'Elizabeth allowed that he had given a very rational account of it, and they continued talking together with mutual satisfaction till supper put an end to cards, and gave the rest of the ladies their share of Mr. Wickham’s attentions. There could be no conversation in the noise of Mrs. Philips’s supper party, but his manners recommended him to everybody. Whatever he said, was said well; and whatever he did, done gracefully. Elizabeth went away with her head full of him. She could think of nothing but of Mr. Wickham, and of what he had told her, all the way home; but there was not time for her even to mention his name as they went, for neither Lydia nor Mr. Collins were once silent. Lydia talked incessantly of lottery tickets, of the fish she had lost and the fish she had won; and Mr. Collins, in describing the civility of Mr. and Mrs. Philips, protesting that he did not in the least regard his losses at whist, enumerating all the dishes at supper, and repeatedly fearing that he crowded his cousins, had more to say than he could well manage before the carriage stopped at Longbourn House.',
            # Melville, Moby-Dick (1851)
            'In connection with this appellative of “Whalebone whales,” it is of great importance to mention, that however such a nomenclature may be convenient in facilitating allusions to some kind of whales, yet it is in vain to attempt a clear classification of the Leviathan, founded upon either his baleen, or hump, or fin, or teeth; notwithstanding that those marked parts or features very obviously seem better adapted to afford the basis for a regular system of Cetology than any other detached bodily distinctions, which the whale, in his kinds, presents. How then? The baleen, hump, back-fin, and teeth; these are things whose peculiarities are indiscriminately dispersed among all sorts of whales, without any regard to what may be the nature of their structure in other and more essential particulars. Thus, the sperm whale and the humpbacked whale, each has a hump; but there the similitude ceases. Then, this same humpbacked whale and the Greenland whale, each of these has baleen; but there again the similitude ceases. And it is just the same with the other parts above mentioned. In various sorts of whales, they form such irregular combinations; or, in the case of any one of them detached, such an irregular isolation; as utterly to defy all general methodization formed upon such a basis. On this rock every one of the whale-naturalists has split.',
            # Franklin, Autobiography (1791)
            "At Burlington I made an acquaintance with many principal people of the province. Several of them had been appointed by the Assembly a committee to attend the press, and take care that no more bills were printed than the law directed. They were therefore, by turns, constantly with us, and generally he who attended, brought with him a friend or two for company. My mind having been much more improv'd by reading than Keimer's, I suppose it was for that reason my conversation seem'd to be more valu'd. They had me to their houses, introduced me to their friends, and show'd me much civility; while he, tho' the master, was a little neglected. In truth, he was an odd fish; ignorant of common life, fond of rudely opposing receiv'd opinions, slovenly to extream dirtiness, enthusiastic in some points of religion, and a little knavish withal.",
            # London, White Fang (1906)
            'The fascination of the light for the grey cub increased from day to day. He was perpetually departing on yard-long adventures toward the cave’s entrance, and as perpetually being driven back. Only he did not know it for an entrance. He did not know anything about entrances—passages whereby one goes from one place to another place. He did not know any other place, much less of a way to get there. So to him the entrance of the cave was a wall—a wall of light. As the sun was to the outside dweller, this wall was to him the sun of his world. It attracted him as a candle attracts a moth. He was always striving to attain it. The life that was so swiftly expanding within him, urged him continually toward the wall of light. The life that was within him knew that it was the one way out, the way he was predestined to tread. But he himself did not know anything about it. He did not know there was any outside at all.',
            # Doyle, The Adventures of Sherlock Holmes (1892)
            'The man who entered was a strange and impressive figure. His slow, limping step and bowed shoulders gave the appearance of decrepitude, and yet his hard, deep-lined, craggy features, and his enormous limbs showed that he was possessed of unusual strength of body and of character. His tangled beard, grizzled hair, and outstanding, drooping eyebrows combined to give an air of dignity and power to his appearance, but his face was of an ashen white, while his lips and the corners of his nostrils were tinged with a shade of blue. It was clear to me at a glance that he was in the grip of some deadly and chronic disease.',
            # Jacob Riis, How the Other Half Lives (1890)
            "With all his conspicuous faults, the swarthy Italian immigrant has his redeeming traits. He is as honest as he is hot-headed. There are no Italian burglars in the Rogues' Gallery; the ex-brigand toils peacefully with pickaxe and shovel on American ground. His boy occasionally shows, as a pick-pocket, the results of his training with the toughs of the Sixth Ward slums. The only criminal business to which the father occasionally lends his hand, outside of murder, is a bunco game, of which his confiding countrymen, returning with their hoard to their native land, are the victims. The women are faithful wives and devoted mothers. Their vivid and picturesque costumes lend a tinge of color to the otherwise dull monotony of the slums they inhabit. The Italian is gay, light-hearted and, if his fur is not stroked the wrong way, inoffensive as a child. His worst offence is that he keeps the stale-beer dives. Where his headquarters is, in the Mulberry Street Bend, these vile dens flourish and gather about them all the wrecks, the utterly wretched, the hopelessly lost, on the lowest slope of depraved humanity. And out of their misery he makes a profit.",
            # Jerome, Three Men in a Boat (1889)
            'On a fine Sunday it presents this appearance nearly all day long, while, up the stream, and down the stream, lie, waiting their turn, outside the gates, long lines of still more boats; and boats are drawing near and passing away, so that the sunny river, from the Palace up to Hampton Church, is dotted and decked with yellow, and blue, and orange, and white, and red, and pink. All the inhabitants of Hampton and Moulsey dress themselves up in boating costume, and come and mouch round the lock with their dogs, and flirt, and smoke, and watch the boats; and, altogether, what with the caps and jackets of the men, the pretty coloured dresses of the women, the excited dogs, the moving boats, the white sails, the pleasant landscape, and the sparkling water, it is one of the gayest sights I know of near this dull old London town.',
        ],
    },
    {
        "name": "score spread",
        "criterion": 2,
        # Target: mean confidence of the 5 AI texts minus mean of the 5 human
        # texts is at least 0.40, in every trial. AI texts first, then human.
        "texts": [
            # AI (Claude)
            'Remote work has fundamentally transformed the way organizations operate in the modern era. By leveraging digital collaboration tools, companies can access a broader talent pool, reduce overhead costs, and offer employees greater flexibility. However, this shift also presents several challenges, including maintaining team cohesion, ensuring effective communication, and preserving a strong company culture. To address these issues, leaders should prioritize regular check-ins, establish clear expectations, and invest in platforms that foster connection. Additionally, it is essential to recognize the importance of work-life balance, as the boundaries between professional and personal life can easily become blurred. Ultimately, the success of remote work depends on a thoughtful approach that balances productivity with employee well-being. By embracing these strategies, organizations can unlock the full potential of a distributed workforce and thrive in an increasingly digital landscape.',
            # AI (Claude)
            'Climate change is one of the most pressing challenges facing humanity today. Rising global temperatures, driven primarily by the burning of fossil fuels, are leading to more frequent and severe weather events, melting ice caps, and rising sea levels. These changes have significant implications for ecosystems, agriculture, and human health. Addressing climate change requires a multifaceted approach that includes transitioning to renewable energy sources, improving energy efficiency, and protecting natural carbon sinks such as forests and wetlands. Furthermore, international cooperation is crucial, as no single nation can solve this problem alone. Individuals can also play a meaningful role by reducing their carbon footprint through sustainable choices. By working together, governments, businesses, and communities can mitigate the impacts of climate change and build a more resilient and sustainable future for generations to come.',
            # AI (Claude)
            'Effective time management is a crucial skill that can significantly enhance both personal and professional success. By prioritizing tasks, setting clear goals, and minimizing distractions, individuals can make the most of their available time. One popular technique is the Pomodoro method, which involves working in focused intervals followed by short breaks. This approach helps maintain concentration and prevents burnout. Another valuable strategy is to break larger projects into smaller, manageable steps, making them less overwhelming and easier to complete. Additionally, it is important to learn to say no to commitments that do not align with your priorities. Regularly reviewing your progress and adjusting your plans can further improve efficiency. Ultimately, mastering time management empowers individuals to achieve their objectives while maintaining a healthy balance between work and personal life.',
            # AI (Claude)
            "Reading offers numerous benefits that extend far beyond simple entertainment. Engaging with books can improve vocabulary, enhance critical thinking skills, and broaden one's understanding of different cultures and perspectives. Studies have shown that regular reading can also reduce stress levels and improve overall mental well-being. Moreover, reading fiction has been linked to increased empathy, as it allows readers to experience the world through the eyes of diverse characters. In an age dominated by digital distractions, setting aside dedicated time for reading can provide a valuable opportunity for reflection and personal growth. Whether it is a classic novel, a thought-provoking nonfiction work, or a collection of poetry, every book has the potential to inspire and educate. Ultimately, cultivating a reading habit is a powerful investment in lifelong learning and self-improvement.",
            # AI (Claude)
            'Artificial intelligence is rapidly reshaping industries across the globe, offering unprecedented opportunities for innovation and efficiency. From healthcare to finance, AI-powered systems are being used to analyze vast amounts of data, automate routine tasks, and support complex decision-making processes. In healthcare, for example, machine learning algorithms can assist doctors in diagnosing diseases more accurately and at earlier stages. However, the widespread adoption of AI also raises important ethical considerations, including concerns about privacy, bias, and job displacement. It is therefore essential for policymakers, developers, and stakeholders to collaborate in establishing robust guidelines that ensure AI is developed and deployed responsibly. By striking the right balance between innovation and accountability, society can harness the transformative power of artificial intelligence while minimizing potential risks and maximizing its benefits for all.',
            # Austen, Pride and Prejudice (1813)
            'Elizabeth related to Jane, the next day, what had passed between Mr. Wickham and herself. Jane listened with astonishment and concern: she knew not how to believe that Mr. Darcy could be so unworthy of Mr. Bingley’s regard; and yet it was not in her nature to question the veracity of a young man of such amiable appearance as Wickham. The possibility of his having really endured such unkindness was enough to interest all her tender feelings; and nothing therefore remained to be done but to think well of them both, to defend the conduct of each, and throw into the account of accident or mistake whatever could not be otherwise explained.',
            # Melville, Moby-Dick (1851)
            'But it may possibly be conceived that, in the internal parts of the whale, in his anatomy—there, at least, we shall be able to hit the right classification. Nay; what thing, for example, is there in the Greenland whale’s anatomy more striking than his baleen? Yet we have seen that by his baleen it is impossible correctly to classify the Greenland whale. And if you descend into the bowels of the various leviathans, why there you will not find distinctions a fiftieth part as available to the systematizer as those external ones already enumerated. What then remains? nothing but to take hold of the whales bodily, in their entire liberal volume, and boldly sort them that way. And this is the Bibliographical system here adopted; and it is the only one that can possibly succeed, for it alone is practicable. To proceed.',
            # Doyle, The Adventures of Sherlock Holmes (1892)
            'When I glance over my notes and records of the Sherlock Holmes cases between the years ’82 and ’90, I am faced by so many which present strange and interesting features that it is no easy matter to know which to choose and which to leave. Some, however, have already gained publicity through the papers, and others have not offered a field for those peculiar qualities which my friend possessed in so high a degree, and which it is the object of these papers to illustrate. Some, too, have baffled his analytical skill, and would be, as narratives, beginnings without an ending, while others have been but partially cleared up, and have their explanations founded rather upon conjecture and surmise than on that absolute logical proof which was so dear to him. There is, however, one of these last which was so remarkable in its details and so startling in its results that I am tempted to give some account of it in spite of the fact that there are points in connection with it which never have been, and probably never will be, entirely cleared up.',
            # Jacob Riis, How the Other Half Lives (1890)
            'These figures speak for themselves, when it is shown that in the model tenement across the way at Nos. 48 and 50, where the same class of people live in greater swarms (161, according to the record), but under good management, and in decent quarters, the hearse called that year only twice, once for a baby. The agent of the Christian people who built that tenement will tell you that Italians are good tenants, while the owner of the alley will oppose every order to put his property in repair with the claim that they are the worst of a bad lot. Both are right, from their different stand-points. It is the stand-point that makes the difference--and the tenant.',
            # London, White Fang (1906)
            'There was one strange thing about this wall of light. His father (he had already come to recognise his father as the one other dweller in the world, a creature like his mother, who slept near the light and was a bringer of meat)—his father had a way of walking right into the white far wall and disappearing. The grey cub could not understand this. Though never permitted by his mother to approach that wall, he had approached the other walls, and encountered hard obstruction on the end of his tender nose. This hurt. And after several such adventures, he left the walls alone. Without thinking about it, he accepted this disappearing into the wall as a peculiarity of his father, as milk and half-digested meat were peculiarities of his mother.',
        ],
    },
    {
        "name": "label coverage",
        "criterion": 3,
        # Target: each of human / unsure / ai appears at least once per trial.
        "texts": [
            # clearly AI (written by Claude for this test)
            'Remote work has fundamentally transformed the way organizations operate in the modern era. By leveraging digital collaboration tools, companies can access a broader talent pool, reduce overhead costs, and offer employees greater flexibility. However, this shift also presents several challenges, including maintaining team cohesion, ensuring effective communication, and preserving a strong company culture. To address these issues, leaders should prioritize regular check-ins, establish clear expectations, and invest in platforms that foster connection. Additionally, it is essential to recognize the importance of work-life balance, as the boundaries between professional and personal life can easily become blurred. Ultimately, the success of remote work depends on a thoughtful approach that balances productivity with employee well-being. By embracing these strategies, organizations can unlock the full potential of a distributed workforce and thrive in an increasingly digital landscape.',
            # edited AI: the remote-work AI text rewritten casually (contractions, short sentences)
            "So remote work changed a lot about how companies run. You can hire from anywhere, you save on office rent, and people get more flexibility, which most of them really like. But it's not all great. Teams drift apart, messages get missed, and the culture kind of fades if nobody works at it. What helped us was regular check-ins and being really clear about who owns what. Also, work and home blur together fast when your desk is in your bedroom, so you have to set some limits. In the end remote work only works if you're thoughtful about it and balance getting stuff done with people actually being okay.",
            # formal human: Thoreau, Walden (1854)
            'The works of the great poets have never yet been read by mankind, for only great poets can read them. They have only been read as the multitude read the stars, at most astrologically, not astronomically. Most men have learned to read to serve a paltry convenience, as they have learned to cipher in order to keep accounts and not be cheated in trade; but of reading as a noble intellectual exercise they know little or nothing; yet this only is reading, in a high sense, not that which lulls us as a luxury and suffers the nobler faculties to sleep the while, but what we have to stand on tip-toe to read and devote our most alert and wakeful hours to.',
            # plain human: Douglass, Narrative of the Life of Frederick Douglass (1845)
            'Mr. Gore was a grave man, and, though a young man, he indulged in no jokes, said no funny words, seldom smiled. His words were in perfect keeping with his looks, and his looks were in perfect keeping with his words. Overseers will sometimes indulge in a witty word, even with the slaves; not so with Mr. Gore. He spoke but to command, and commanded but to be obeyed; he dealt sparingly with his words, and bountifully with his whip, never using the former where the latter would answer as well. When he whipped, he seemed to do so from a sense of duty, and feared no consequences. He did nothing reluctantly, no matter how disagreeable; always at his post, never inconsistent. He never promised but to fulfil. He was, in a word, a man of the most inflexible firmness and stone-like coolness.',
            # casual human: Jerome, Three Men in a Boat (1889)
            'George has bought some new things for this trip, and I’m rather vexed about them. The blazer is loud. I should not like George to know that I thought so, but there really is no other word for it. He brought it home and showed it to us on Thursday evening. We asked him what colour he called it, and he said he didn’t know. He didn’t think there was a name for the colour. The man had told him it was an Oriental design. George put it on, and asked us what we thought of it. Harris said that, as an object to hang over a flower-bed in early spring to frighten the birds away, he should respect it; but that, considered as an article of dress for any human being, except a Margate nigger, it made him ill. George got quite huffy; but, as Harris said, if he didn’t want his opinion, why did he ask for it?',
            # borderline: human sentences around two AI sentences
            "I started running last spring mostly because my doctor told me to. The first week was awful and I quit twice. Regular physical activity offers numerous benefits for both physical and mental health, including improved cardiovascular fitness, better sleep quality, and reduced stress levels. By establishing a consistent routine and setting achievable goals, individuals can gradually build endurance and confidence. Anyway, I can run three miles now without stopping, which still surprises me, and my knees mostly don't hurt.",
        ],
    },
    {
        "name": "appeal path",
        "criterion": 4,
        # Target: 10 of 10 appeals return 200 + under_review, add exactly one
        # appeal entry, leave the decision entry intact; the made-up id gets a
        # 404 and no appeal entry. Reuses criterion 1's texts (other creator_ids).
        "appeal": True,
        "fake_appeals": 1,
        "texts": [
            # Douglass, Narrative of the Life of Frederick Douglass (1845)
            'The colonel, after ascertaining where the slave belonged, rode on; the man also went on about his business, not dreaming that he had been conversing with his master. He thought, said, and heard nothing more of the matter, until two or three weeks afterwards. The poor man was then informed by his overseer that, for having found fault with his master, he was now to be sold to a Georgia trader. He was immediately chained and handcuffed; and thus, without a moment’s warning, he was snatched away, and forever sundered, from his family and friends, by a hand more unrelenting than death. This is the penalty of telling the truth, of telling the simple truth, in answer to a series of plain questions.',
            # Baum, The Wonderful Wizard of Oz (1900)
            'They now came upon more and more of the big scarlet poppies, and fewer and fewer of the other flowers; and soon they found themselves in the midst of a great meadow of poppies. Now it is well known that when there are many of these flowers together their odor is so powerful that anyone who breathes it falls asleep, and if the sleeper is not carried away from the scent of the flowers, he sleeps on and on forever. But Dorothy did not know this, nor could she get away from the bright red flowers that were everywhere about; so presently her eyes grew heavy and she felt she must sit down to rest and to sleep.',
            # Thoreau, Walden (1854)
            'With a little more deliberation in the choice of their pursuits, all men would perhaps become essentially students and observers, for certainly their nature and destiny are interesting to all alike. In accumulating property for ourselves or our posterity, in founding a family or a state, or acquiring fame even, we are mortal; but in dealing with truth we are immortal, and need fear no change nor accident. The oldest Egyptian or Hindoo philosopher raised a corner of the veil from the statue of the divinity; and still the trembling robe remains raised, and I gaze upon as fresh a glory as he did, since it was I in him that was then so bold, and it is he in me that now reviews the vision. No dust has settled on that robe; no time has elapsed since that divinity was revealed. That time which we really improve, or which is improvable, is neither past, present, nor future.',
            # Austen, Pride and Prejudice (1813)
            'Elizabeth allowed that he had given a very rational account of it, and they continued talking together with mutual satisfaction till supper put an end to cards, and gave the rest of the ladies their share of Mr. Wickham’s attentions. There could be no conversation in the noise of Mrs. Philips’s supper party, but his manners recommended him to everybody. Whatever he said, was said well; and whatever he did, done gracefully. Elizabeth went away with her head full of him. She could think of nothing but of Mr. Wickham, and of what he had told her, all the way home; but there was not time for her even to mention his name as they went, for neither Lydia nor Mr. Collins were once silent. Lydia talked incessantly of lottery tickets, of the fish she had lost and the fish she had won; and Mr. Collins, in describing the civility of Mr. and Mrs. Philips, protesting that he did not in the least regard his losses at whist, enumerating all the dishes at supper, and repeatedly fearing that he crowded his cousins, had more to say than he could well manage before the carriage stopped at Longbourn House.',
            # Melville, Moby-Dick (1851)
            'In connection with this appellative of “Whalebone whales,” it is of great importance to mention, that however such a nomenclature may be convenient in facilitating allusions to some kind of whales, yet it is in vain to attempt a clear classification of the Leviathan, founded upon either his baleen, or hump, or fin, or teeth; notwithstanding that those marked parts or features very obviously seem better adapted to afford the basis for a regular system of Cetology than any other detached bodily distinctions, which the whale, in his kinds, presents. How then? The baleen, hump, back-fin, and teeth; these are things whose peculiarities are indiscriminately dispersed among all sorts of whales, without any regard to what may be the nature of their structure in other and more essential particulars. Thus, the sperm whale and the humpbacked whale, each has a hump; but there the similitude ceases. Then, this same humpbacked whale and the Greenland whale, each of these has baleen; but there again the similitude ceases. And it is just the same with the other parts above mentioned. In various sorts of whales, they form such irregular combinations; or, in the case of any one of them detached, such an irregular isolation; as utterly to defy all general methodization formed upon such a basis. On this rock every one of the whale-naturalists has split.',
            # Franklin, Autobiography (1791)
            "At Burlington I made an acquaintance with many principal people of the province. Several of them had been appointed by the Assembly a committee to attend the press, and take care that no more bills were printed than the law directed. They were therefore, by turns, constantly with us, and generally he who attended, brought with him a friend or two for company. My mind having been much more improv'd by reading than Keimer's, I suppose it was for that reason my conversation seem'd to be more valu'd. They had me to their houses, introduced me to their friends, and show'd me much civility; while he, tho' the master, was a little neglected. In truth, he was an odd fish; ignorant of common life, fond of rudely opposing receiv'd opinions, slovenly to extream dirtiness, enthusiastic in some points of religion, and a little knavish withal.",
            # London, White Fang (1906)
            'The fascination of the light for the grey cub increased from day to day. He was perpetually departing on yard-long adventures toward the cave’s entrance, and as perpetually being driven back. Only he did not know it for an entrance. He did not know anything about entrances—passages whereby one goes from one place to another place. He did not know any other place, much less of a way to get there. So to him the entrance of the cave was a wall—a wall of light. As the sun was to the outside dweller, this wall was to him the sun of his world. It attracted him as a candle attracts a moth. He was always striving to attain it. The life that was so swiftly expanding within him, urged him continually toward the wall of light. The life that was within him knew that it was the one way out, the way he was predestined to tread. But he himself did not know anything about it. He did not know there was any outside at all.',
            # Doyle, The Adventures of Sherlock Holmes (1892)
            'The man who entered was a strange and impressive figure. His slow, limping step and bowed shoulders gave the appearance of decrepitude, and yet his hard, deep-lined, craggy features, and his enormous limbs showed that he was possessed of unusual strength of body and of character. His tangled beard, grizzled hair, and outstanding, drooping eyebrows combined to give an air of dignity and power to his appearance, but his face was of an ashen white, while his lips and the corners of his nostrils were tinged with a shade of blue. It was clear to me at a glance that he was in the grip of some deadly and chronic disease.',
            # Jacob Riis, How the Other Half Lives (1890)
            "With all his conspicuous faults, the swarthy Italian immigrant has his redeeming traits. He is as honest as he is hot-headed. There are no Italian burglars in the Rogues' Gallery; the ex-brigand toils peacefully with pickaxe and shovel on American ground. His boy occasionally shows, as a pick-pocket, the results of his training with the toughs of the Sixth Ward slums. The only criminal business to which the father occasionally lends his hand, outside of murder, is a bunco game, of which his confiding countrymen, returning with their hoard to their native land, are the victims. The women are faithful wives and devoted mothers. Their vivid and picturesque costumes lend a tinge of color to the otherwise dull monotony of the slums they inhabit. The Italian is gay, light-hearted and, if his fur is not stroked the wrong way, inoffensive as a child. His worst offence is that he keeps the stale-beer dives. Where his headquarters is, in the Mulberry Street Bend, these vile dens flourish and gather about them all the wrecks, the utterly wretched, the hopelessly lost, on the lowest slope of depraved humanity. And out of their misery he makes a profit.",
            # Jerome, Three Men in a Boat (1889)
            'On a fine Sunday it presents this appearance nearly all day long, while, up the stream, and down the stream, lie, waiting their turn, outside the gates, long lines of still more boats; and boats are drawing near and passing away, so that the sunny river, from the Palace up to Hampton Church, is dotted and decked with yellow, and blue, and orange, and white, and red, and pink. All the inhabitants of Hampton and Moulsey dress themselves up in boating costume, and come and mouch round the lock with their dogs, and flirt, and smoke, and watch the boats; and, altogether, what with the caps and jackets of the men, the pretty coloured dresses of the women, the excited dogs, the moving boats, the white sails, the pleasant landscape, and the sparkling water, it is one of the gayest sights I know of near this dull old London town.',
        ],
    },
    {
        "name": "bad input",
        "criterion": 5,
        # Target: each returns a 4xx JSON error (never a 500) and adds exactly
        # one `rejected` entry to the audit log.
        "bodies": [
            {"text": "", "creator_id": "eval_bad_empty"},
            {"text": "   \n\t  ", "creator_id": "eval_bad_spaces"},
            {"creator_id": "eval_bad_missing"},
            {"text": None, "creator_id": "eval_bad_null"},
            {"text": 12345, "creator_id": "eval_bad_number"},
            {"text": "word " * 50000, "creator_id": "eval_bad_huge"},
            {"text": "At Burlington I made an acquaintance with many principal people of the province. Several of them had been appointed by the Assembly a committee to attend the press, and take care that no more bills were printed than the law directed. They were therefore, by turns, constantly with us, and generally he who attended, brought with him a friend or two for company. My mind having been much more improv'd by reading than Keimer's, I suppose it was for that reason my conversation seem'd to be more valu'd. They had me to their houses, introduced me to their friends, and show'd me much civility; while he, tho' the master, was a little neglected. In truth, he was an odd fish; ignorant of common life, fond of rudely opposing receiv'd opinions, slovenly to extream dirtiness, enthusiastic in some points of religion, and a little knavish withal."},
        ],
    },
]


def validate() -> list[str]:
    """
    Complain about anything malformed, before a long run rather than during.

    A "bodies" scenario is deliberately exempt from the empty check — an empty
    string is the whole point of a bad-input case, and refusing to run one
    would make that criterion untestable.
    """
    problems = []
    for i, scenario in enumerate(SCENARIOS, 1):
        if not scenario.get("name"):
            problems.append(f"scenario {i} has no name")

        texts = scenario.get("texts")
        bodies = scenario.get("bodies")

        if texts and bodies:
            problems.append(
                f"scenario {i} ('{scenario.get('name')}') has both texts and "
                f"bodies — pick one"
            )
            continue

        if bodies:
            for j, body in enumerate(bodies, 1):
                if not isinstance(body, dict):
                    problems.append(
                        f"scenario {i}, body {j} is not a dict — bodies are whole "
                        f"request bodies, like {{'text': '', 'creator_id': 'x'}}"
                    )
            continue

        if not texts:
            problems.append(f"scenario {i} has no texts and no bodies")
            continue

        for j, text in enumerate(texts, 1):
            if not str(text).strip():
                problems.append(
                    f"scenario {i}, text {j} is empty — if an empty submission is what "
                    f"you're testing, use 'bodies' instead of 'texts'"
                )
            elif str(text).startswith("REPLACE ME"):
                problems.append(
                    f"scenario {i} ('{scenario.get('name')}'), text {j} is still "
                    f"the placeholder"
                )
    return problems
