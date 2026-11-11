# Customer reviews and purchase risk

A literature review for our Amazon India feature

SC4025 Digital Product Management | 1 November 2026

## Introduction

When people shop online, they have to judge a product before they can see or try it. Customer reviews help fill that gap by describing what earlier buyers received and experienced. For our Amazon India feature, we want to find reviews that raise concerns about fake products, wrong items or products that differ from their descriptions.

This review explains what earlier studies tell us about using reviews for that purpose. It brings together research on trust, counterfeit detection, the meaning of review text, fake reviews and changes in ratings over time. We also look at Indian consumer research to understand why the feature could be useful to shoppers. The studies guide our approach, while the star filter, thresholds and synthetic examples are choices we have made for our own project. We draw on the available papers, author manuscripts and study summaries published by journals and universities.

## Why trust matters when people shop online

Pavlou studied how trust, risk, usefulness and ease of use affect online shopping. He tested his model in two studies involving 103 students and 155 online consumers. The results supported the view that trust and perceived risk help explain people's willingness to buy online. [1](https://www.tandfonline.com/doi/abs/10.1080/10864415.2003.11044275) This matters for our project because a shopper may like a product but still hesitate if they are unsure whether the seller will deliver what was promised.

Gefen, Karahanna and Straub reached a similar conclusion through their study of experienced online shoppers. They found that trust in the seller matters alongside how useful and easy the website is to use. They also linked trust to familiar website design and the belief that safeguards are in place. [2](https://aisel.aisnet.org/misq/vol27/iss1/4/) While Pavlou explains why uncertainty affects a purchase, Gefen and his colleagues give more attention to how the shopping experience can build trust.

These studies suggest that our feature should help shoppers understand a concern as well as draw their attention to it. [1](https://www.tandfonline.com/doi/abs/10.1080/10864415.2003.11044275) [2](https://aisel.aisnet.org/misq/vol27/iss1/4/) A warning is more useful when the shopper can see why it appeared and read the comments behind it. We therefore plan to use clear wording and show the supporting reviews. When we test the feature, we will check whether shoppers understand the result and whether it helps them make a better-informed decision.

## Using reviews to identify possible counterfeit products

Wimmer and Yoon developed OnCDS, a system that uses customer reviews to produce a counterfeit score. It uses sentiment analysis, which examines positive and negative wording, together with methods for finding useful words and topics in reviews. The researchers also studied how the score affected trust, perceived risk and attitudes towards buying. Their results linked the score to these customer responses. [3](https://scholars.georgiasouthern.edu/en/publications/counterfeit-product-detection-bridging-the-gap-between-design-sci-3/) This gives our project a useful example of both analysing reviews and studying how shoppers use the result.

Cao also used Amazon reviews to estimate which listings might be selling counterfeit products. The study focused on men's fragrances and wireless phone chargers. Cao connected these estimates with buying behaviour and used an Amazon anti-counterfeit programme as another way to study the problem. The findings suggested that sharing detection results with customers could help genuine sellers and the platform. [4](https://escholarship.org/uc/item/5v85s1fm) This supports our goal of making useful risk information available before a purchase.

Both studies show that reviews are worth investigating as a source of counterfeit concerns, but they focus on different parts of the problem. Wimmer and Yoon look closely at the score and the shopper's response to it. Cao also considers differences between products and the wider effect on the market. [3](https://scholars.georgiasouthern.edu/en/publications/counterfeit-product-detection-bridging-the-gap-between-design-sci-3/) [4](https://escholarship.org/uc/item/5v85s1fm) Together, they suggest that our evaluation should cover both the quality of the result and how customers respond to it.

We use these studies as a starting point for our approach. Their findings support looking for meaningful patterns in review text. [3](https://scholars.georgiasouthern.edu/en/publications/counterfeit-product-detection-bridging-the-gap-between-design-sci-3/) [4](https://escholarship.org/uc/item/5v85s1fm) Our next step is to test which patterns work in our datasets and how they can be explained clearly to shoppers.

## Understanding what a negative review means

A low rating tells us that a buyer was unhappy, but the reason for that rating is important. Pontiki and her colleagues studied aspect-based sentiment analysis, which looks at what part of a product or service a review discusses and how the reviewer feels about it. Their work used restaurant and laptop reviews, where a customer could praise one feature and criticise another in the same review. [5](https://aclanthology.org/S14-2004.pdf) This shows why an overall positive or negative label can miss useful detail.

We apply that idea by separating complaints about authenticity from complaints about receiving the wrong item or finding that the description was inaccurate. [5](https://aclanthology.org/S14-2004.pdf) For example, a review saying that a product broke quickly describes a different concern from one saying that the label does not match the product page. Reading the reason behind the complaint helps us decide which category it belongs to.

This is why our method combines one- and two-star ratings with review wording. The rating helps us find dissatisfied buyers, while the text helps us understand their experience. We chose this as the first screen for our project and will test how well it finds relevant complaints. Reviews with higher ratings can also mention problems, so checking those reviews later will help us understand what the first screen may miss.

## Why we need to check the reviews behind a listing

He and his colleagues studied Amazon products whose sellers had been observed buying reviews. They found links between these products through shared reviewers, which helped them identify review buying. [6](https://arxiv.org/abs/2410.17507) Their work shows why several positive or negative comments may need closer checking before we treat them as separate customer experiences.

This adds another layer to the work by Wimmer and Yoon and by Cao. Those studies use reviews to assess possible counterfeits. He and his colleagues ask whether the reviews themselves can be trusted. [3](https://scholars.georgiasouthern.edu/en/publications/counterfeit-product-detection-bridging-the-gap-between-design-sci-3/) [4](https://escholarship.org/uc/item/5v85s1fm) [6](https://arxiv.org/abs/2410.17507) Our feature needs to consider both questions. A pattern of similar complaints is more useful when the comments provide different accounts of the same problem.

We therefore look at the whole listing after the first screen. We compare low and high ratings, read the relevant complaints and check for copied text. Where reviewer identities are available, we can also check whether the comments come from different accounts. Our 25% low-star threshold is a starting point chosen for the prototype. We compare it with other thresholds to see which is useful, while keeping the meaning of the complaints central to the decision.

## What changes in ratings over time can tell us

Li and Hitt studied why product ratings can change over time. Using Amazon book reviews, they examined how early buyers may have different preferences from people who buy later. Their findings showed that changes in the group of buyers can affect ratings even when the product itself has not changed. [7](https://pubsonline.informs.org/doi/10.1287/isre.1070.0154) Although their study focused on books, it gives us a useful reason to look beyond the rating trend alone.

For our project, a fall in ratings is a reason to read the newer complaints and see what has changed. [7](https://pubsonline.informs.org/doi/10.1287/isre.1070.0154) If more buyers begin describing the same authenticity or product-mismatch problem, that pattern may be worth highlighting. We will compare the share of relevant complaints in earlier and later periods and check that both periods contain enough reviews. These periods follow the dates in the dataset. For a listing whose records end in 2020, the comparison would be between periods within that history.

## Building and checking our screening method

Ratner and his colleagues developed Snorkel, a system that uses rules to help label data. This approach is known as weak supervision. The system allows for rules to be wrong or to overlap with one another. [8](https://arxiv.org/abs/1711.10160) This helps us think about our keyword screen. A review that matches several similar words still needs to be read for its meaning, because those matches may all point to the same statement.

Guo and his colleagues studied a different problem. They found that a model can express more confidence in its predictions than its actual performance supports. They also tested ways to improve the match between confidence and correctness. [9](https://proceedings.mlr.press/v70/guo17a.html) For our feature, this becomes important if we later display a percentage or probability. We would need to check that the number gives shoppers a fair picture of how reliable the prediction is.

These studies help us plan how to improve the feature step by step. [8](https://arxiv.org/abs/1711.10160) [9](https://proceedings.mlr.press/v70/guo17a.html) We can start with clear rating and wording rules, ask independent readers to check the comments, and compare the results. As the method improves, we can assess whether a numerical score is useful. A label showing that a review contains a counterfeit complaint will need different checks from a claim that the delivered product has been confirmed as fake.

Our synthetic data helps us test the first part of this process. We can create examples with a single complaint, repeated complaints, copied comments or a change over time and check how the code responds. These examples make it easier to find problems in the method before we test it on more real reviews. We keep the synthetic examples separate so that our conclusions about real products continue to come from real evidence.

## Why this research matters for Amazon India

PwC's Indian consumer study included an online survey of 2,100 people, along with interviews. It found that 37% of urban respondents saw fake reviews as a barrier to trying other shopping platforms for electronics. [10](https://www.pwc.in/industries/retail-and-consumer/how-india-shops-online.html) This shows that the reliability of reviews can affect how shoppers judge a platform. It strengthens the case for showing customers the comments behind our result so they can understand and judge the concern for themselves.

Bain and Flipkart estimate that India's online retail market served 290-300 million shoppers and generated USD 65-66 billion in sales value in 2025. [11](https://storage.googleapis.com/flipkart-stories-media/How_India_Shops_Online_2026_060094273e/How_India_Shops_Online_2026_060094273e.pdf) Although these figures cover the whole Indian market, they show the size of the market that Amazon India can grow within. As more people shop online, helping them judge product quality and authenticity could be one way for Amazon to improve their experience. Our feature addresses a specific part of that opportunity by making relevant review information easier to use.

The two reports support the project in different ways. PwC helps explain why trust in shopping information matters to Indian consumers. Bain and Flipkart show the size of the market in which that need exists. [10](https://www.pwc.in/industries/retail-and-consumer/how-india-shops-online.html) [11](https://storage.googleapis.com/flipkart-stories-media/How_India_Shops_Online_2026_060094273e/How_India_Shops_Online_2026_060094273e.pdf) Read alongside the academic studies, they give us a reason to investigate the feature and test whether it helps shoppers make decisions.

## How our project builds on the literature

The studies give us a clear way to connect our idea with earlier research. The trust studies explain why shoppers need information they can understand and rely on. The counterfeit-detection studies show how reviews can be used to investigate authenticity concerns. The studies on review meaning, fake reviews and changing ratings help us decide what to check before we highlight a listing.

We bring these ideas together using Indian Products on Amazon as our main dataset and Amazon Reviews 2023 as a secondary comparison. Our method starts with low ratings and relevant wording, then looks at the other reviews, repeated complaints and changes within the listing's history. This lets us investigate whether the combined evidence gives a more useful picture than one bad review alone.

Our first version will explain why a listing has been highlighted and show the reviews behind that result. We can then test whether shoppers find the information clear and useful, alongside checking how well the method finds the intended complaints. This gives us a practical way to build on the literature and work towards better estimates of purchase risk.

## References

[1] Pavlou, P. A. (2003). *Consumer Acceptance of Electronic Commerce. Integrating Trust and Risk with the Technology Acceptance Model*. International Journal of Electronic Commerce, 7(3), 101-134. [Publisher record](https://www.tandfonline.com/doi/abs/10.1080/10864415.2003.11044275).

[2] Gefen, D., Karahanna, E., and Straub, D. W. (2003). *Trust and TAM in Online Shopping. An Integrated Model*. MIS Quarterly, 27(1), 51-90. [Journal record](https://aisel.aisnet.org/misq/vol27/iss1/4/).

[3] Wimmer, H., and Yoon, V. Y. (2017). *Counterfeit product detection. Bridging the gap between design science and behavioral science in information systems research*. Decision Support Systems, 104, 1-12. [University publication record](https://scholars.georgiasouthern.edu/en/publications/counterfeit-product-detection-bridging-the-gap-between-design-sci-3/).

[4] Cao, Z. (2023). *An Empirical Examination of Deceptive Counterfeiting Activities in Electronic Markets*. Doctoral dissertation, University of California, Irvine. [Repository](https://escholarship.org/uc/item/5v85s1fm).

[5] Pontiki, M., et al. (2014). *SemEval-2014 Task 4. Aspect Based Sentiment Analysis*. Proceedings of SemEval 2014, 27-35. [Paper](https://aclanthology.org/S14-2004.pdf).

[6] He, S., Hollenbeck, B., Overgoor, G., Proserpio, D., and Tosyali, A. (2022). *Detecting fake-review buyers using network structure. Direct evidence from Amazon*. PNAS, 119(47), e2211932119. [Author manuscript posted in 2024](https://arxiv.org/abs/2410.17507).

[7] Li, X., and Hitt, L. M. (2008). *Self-Selection and Information Role of Online Product Reviews*. Information Systems Research, 19(4), 456-474. [Publisher record](https://pubsonline.informs.org/doi/10.1287/isre.1070.0154).

[8] Ratner, A., et al. (2017). *Snorkel. Rapid Training Data Creation with Weak Supervision*. Proceedings of the VLDB Endowment, 11(3), 269-282. [Manuscript](https://arxiv.org/abs/1711.10160).

[9] Guo, C., Pleiss, G., Sun, Y., and Weinberger, K. Q. (2017). *On Calibration of Modern Neural Networks*. Proceedings of ICML, 70, 1321-1330. [Paper](https://proceedings.mlr.press/v70/guo17a.html).

[10] PwC India. (2024). *How India shops online*. [Study](https://www.pwc.in/industries/retail-and-consumer/how-india-shops-online.html).

[11] Bain & Company and Flipkart. (2026). *How India Shops Online 2026*. [Report](https://storage.googleapis.com/flipkart-stories-media/How_India_Shops_Online_2026_060094273e/How_India_Shops_Online_2026_060094273e.pdf).
