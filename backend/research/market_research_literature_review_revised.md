# Making Amazon India purchases safer

Market research and literature review for our proposed feature

SC4025 Digital Product Management | 1 November 2026

## Our proposed feature

We want to help Amazon India shoppers judge whether a product may be fake, arrive as the wrong item or differ from its description. The feature will bring together relevant customer reviews and show why a listing has been highlighted. A shopper will be able to read the comments behind the result and see whether the same concern appears repeatedly or becomes more common over time.

Earlier studies give us a useful starting point because they have already explored how reviews can be used to estimate counterfeit risk. Research on trust also helps explain how shoppers may respond to that information. We use these findings to guide the feature, then test our own method on the data available to us.

Our first version will highlight possible concerns and explain the evidence behind them. As we collect better data and check the method's performance, we can work towards more precise estimates of purchase risk.

## The customer problem and market opportunity

A shopper may like the price and appearance of a product but still wonder whether it will be genuine or match the pictures. Reviews can help answer those questions, although finding the useful comments can take time. Our feature aims to make that information easier to find by bringing related complaints together and explaining the pattern.

PwC's Indian consumer study included an online survey of 2,100 people and several forms of interviews. It found that 37% of urban respondents saw fake reviews as a barrier to trying other platforms for electronics purchases. [1](https://www.pwc.in/industries/retail-and-consumer/how-india-shops-online.html) This suggests that shoppers care about whether the information they read can be trusted. We therefore want customers to see the comments behind a concern and understand why it has been raised.

Bain and Flipkart estimate that India's online retail market served 290-300 million shoppers and generated USD 65-66 billion in sales value in 2025. They expect the market to reach USD 170-180 billion by 2030. [2](https://storage.googleapis.com/flipkart-stories-media/How_India_Shops_Online_2026_060094273e/How_India_Shops_Online_2026_060094273e.pdf) Although these estimates cover India's whole market, they show the growth that Amazon India can take part in. Helping shoppers feel better informed about products could be one way for Amazon to improve the experience it offers as that market grows.

We are starting with branded products where authenticity and product details affect the buying decision. Indian Products on Amazon gives us examples from personal care and other consumer goods. These examples allow us to build the first version and ask shoppers which types of products they would most want help with.

## What earlier research tells us

Wimmer and Yoon developed OnCDS, a system that reads customer reviews and produces a counterfeit score. It uses methods for analysing positive and negative wording and finding useful words and topics. The researchers also studied how the score affected trust, perceived risk and attitudes towards buying. [3](https://scholars.georgiasouthern.edu/en/publications/counterfeit-product-detection-bridging-the-gap-between-design-sci-3/) Their work supports our decision to investigate both the review patterns and the way customers use the result.

Cao also used Amazon reviews to estimate counterfeit risk, focusing on men's fragrances and wireless phone chargers. The study linked these estimates with buying behaviour and differences between products. [4](https://escholarship.org/uc/item/5v85s1fm) This suggests that we should pay attention to what customers describe in each category. A complaint about the smell of a fragrance may have a different meaning from a complaint about how a charger works.

The two studies support using reviews as a starting point, while showing that the result needs to make sense to the shopper. [3](https://scholars.georgiasouthern.edu/en/publications/counterfeit-product-detection-bridging-the-gap-between-design-sci-3/) [4](https://escholarship.org/uc/item/5v85s1fm) We therefore want to explain the concern and show its supporting comments. We will test whether that helps customers make a decision, as well as checking whether the method finds the right complaints.

Pavlou studied trust and perceived risk alongside how useful and easy an online shopping service is to use. Gefen, Karahanna and Straub also found that trust matters to experienced online shoppers. [5](https://www.tandfonline.com/doi/abs/10.1080/10864415.2003.11044275) [6](https://aisel.aisnet.org/misq/vol27/iss1/4/) These findings support placing the feature within the familiar review section and using language that customers can understand quickly.

Pontiki and her colleagues studied how a review can express different opinions about different parts of a product or service. [7](https://aclanthology.org/S14-2004/) We apply this idea by separating authenticity concerns from wrong-item and description complaints. For example, a comment saying that a product broke is different from one saying that the received label does not match the listing. That difference helps us explain the type of problem to the shopper.

He and his colleagues studied products whose sellers were observed buying reviews. They found links through shared reviewers that helped identify review buying. [8](https://arxiv.org/abs/2410.17507) Their work gives us a reason to check whether several comments offer different experiences or simply repeat the same text. A high number of matching comments is more useful when those comments provide separate accounts of the concern.

Ratner and his colleagues show how simple rules can help label data while allowing for mistakes and overlap between the rules. [9](https://arxiv.org/abs/1711.10160) We use this idea when checking our keywords. Guo and his colleagues show why a model's stated confidence should also be checked against its actual results. [10](https://proceedings.mlr.press/v70/guo17a.html) Together, these studies guide us towards a first version with clear rules and supporting comments, followed by careful testing before we add more precise scores.

## How we developed our method

We looked for data that links each review to its own rating and date. The original Amazon Sales catalogue combined several reviews in one field, so it was more useful for studying product information. We chose Indian Products on Amazon as the main review dataset and used Amazon Reviews 2023 as a second source for comparison. [15](https://www.kaggle.com/datasets/nehaprabhavalkar/indian-products-on-amazon) [16](https://huggingface.co/datasets/McAuley-Lab/Amazon-Reviews-2023) [17](https://www.kaggle.com/datasets/karkavelrajaj/amazon-sales-dataset)

After cleaning, the main dataset contains 1,388 reviews across 145 product identifiers, known as ASINs. Of these reviews, 338 have one or two stars. Our general Amazon sample contains 39,986 usable reviews. Working with both sources helped us try the same method on different collections. The Indian-products file gives us relevant product examples, although it does not state the marketplace or country of every reviewer. [18]

Our first screen combines a one- or two-star rating with selected review wording. In the main dataset, 77 low-star reviews matched the wording, including 42 with specific authenticity or mismatch terms. We used AI to help check the meaning of those matches and retained 39 reviews describing relevant concerns. [18] This helped us separate comments such as poor quality from comments about a possible fake or a difference between the product and its description.

We then looked at the other reviews for each listing. This matters because a single complaint and a repeated problem should be treated differently. We compare one- and two-star reviews with four- and five-star reviews, while reporting three-star reviews separately. We also read the relevant comments and check whether they describe similar problems in different words.

For the prototype, we start with a threshold of 25% low-star reviews among the low- and high-star groups. We require at least 20 reviews in those groups before applying it and compare the result with 20% and 30% thresholds. These are our trial choices. Testing different values will help us decide whether the threshold is useful when combined with the review content.

We also compare earlier and later reviews within the dataset. A listing may have many older positive comments while later buyers report a different experience. Our first test uses two consecutive 90-day periods ending at the listing's last recorded review. We compare the share of relevant complaints as well as their number, so an increase in all reviews is not mistaken for an increase in complaints.

The real data helped us identify where we needed more examples to test the code. Most listings in the main dataset have only ten reviews, which is too few for our chosen ten-review minimum in each period. We therefore created a separate synthetic dataset based on patterns in the main source. AI helped us plan the examples, and Python code generated 10,920 reviews across 100 fictional listings. [18]

These examples let us test isolated complaints, repeated concerns, changes over time and copied reviews. They showed why a rating threshold needs to be read together with the complaint text. For example, a listing can have many complaints about poor quality without any claim that the product is fake. The synthetic data helps us check how the method behaves, while our findings about real listings continue to use the real reviews. [18]

## How the feature compares with existing services

Amazon's review highlights summarise common themes, while Rufus answers shopping questions using listing details, reviews and community questions. [11](https://press.aboutamazon.com/in/2023/12/amazon-in-improves-customer-reviews-experience-with-generative-ai) [12](https://www.aboutamazon.in/news/retail/rufus-ai-shopping-assistant-launch-in-india) Our feature builds on the idea of helping customers understand product information. It gives authenticity and mismatch concerns a clear place in the review experience and brings the supporting comments together. We will compare it with ordinary review browsing to see whether it helps shoppers find the relevant information more easily.

Amazon Transparency uses unique codes to help check the authenticity of enrolled products. [13](https://sell.amazon.in/brand-registry/transparency) This provides a useful example of linking a claim about a product to evidence the customer can inspect. Our feature would add information from previous buyers during the shopping stage. In a later version, checks such as Transparency could provide further evidence alongside the reviews.

Flipkart's Open Box Delivery lets customers inspect eligible products before accepting them. They can check for damage and whether the correct item has arrived. [14](https://stories.flipkart.com/open-box-delivery-flipkart-customer-trust) It tackles a related problem at delivery, while our feature helps shoppers judge the available information before ordering. The two approaches show how protection can be offered at different points in the purchase.

These comparisons give us clear features to work towards. Our result should be available before purchase, explain the type of concern, show supporting reviews and describe any change over time. It should also tell the shopper when there are too few reviews for a useful comparison.

## SWOT analysis

Our main strength is a clear customer problem supported by earlier research. We can connect a warning to the comments that produced it, which makes the result easier for shoppers to inspect. This also gives us specific things to test, such as whether customers understand the concern and can find the relevant evidence.

Our main weakness is the amount of detail available in the public datasets. They contain customer reports, but they do not confirm which delivered products were counterfeit or identify the seller behind each order. We will need more complete histories and independent checks of the review labels as the project develops. For the first version, we handle missing information by explaining what the available reviews allow us to say.

The main opportunity is to help customers make better use of information already available during shopping. A later version could combine reviews with complaint records, seller information and authenticity checks if Amazon provides access to them. We could also extend the feature to more categories and Indian languages after testing the first version.

A major threat is that fake or copied reviews could distort the result. Sellers and product versions can also change, and an unnecessary warning could discourage a legitimate purchase. These risks give us a reason to check repeated text, show the supporting comments and test missed concerns alongside incorrect warnings.

## Market size and business value

Bain and Flipkart's estimate of 290-300 million annual online shoppers gives us a broad starting point for the total addressable market, or TAM. [2](https://storage.googleapis.com/flipkart-stories-media/How_India_Shops_Online_2026_060094273e/How_India_Shops_Online_2026_060094273e.pdf) The serviceable market, or SAM, is the smaller group using Amazon India in categories covered by the feature. The obtainable market, or SOM, is the group we could expect to reach during the first year.

To build a planning range, we use the national midpoint of 295 million shoppers. We assume that Amazon reaches 25-40% of them and that 20-30% shop in eligible categories. This gives about 15-35 million potentially serviceable shoppers. If 1-2% of that group uses the feature in the first year, the obtainable audience would be about 150,000-700,000 shoppers. These percentages are our planning assumptions, which we can refine once we have Amazon usage figures and pilot results.

We would judge the business value by whether the feature helps people avoid disappointing purchases and find useful information more quickly. We can measure this through decision quality, time spent finding evidence, complaints and repeat use. These results would help us decide whether the feature is worth expanding.

## What we will test first

The first version will combine low-star wording, the wider rating pattern, repeated complaints and changes within the review history. It will explain the concern and show the comments behind it. When the history is too short for a useful comparison, the result will say so in plain language.

We will ask shoppers to compare this experience with the existing way of reading reviews. We want to find out whether they understand the result, identify relevant concerns more accurately and reach a decision with less effort. We will also compare the screening results with independent checks of the review text. This will help us improve the method before we move towards more precise risk estimates.

## References

[1] PwC India. (2024). *How India shops online*. [Study](https://www.pwc.in/industries/retail-and-consumer/how-india-shops-online.html).
[2] Bain & Company and Flipkart. (2026). *How India Shops Online 2026*. [Report](https://storage.googleapis.com/flipkart-stories-media/How_India_Shops_Online_2026_060094273e/How_India_Shops_Online_2026_060094273e.pdf).
[3] Wimmer, H., and Yoon, V. Y. (2017). *Counterfeit product detection*. Decision Support Systems, 104, 1-12. [University record and abstract](https://scholars.georgiasouthern.edu/en/publications/counterfeit-product-detection-bridging-the-gap-between-design-sci-3/).
[4] Cao, Z. (2023). *An Empirical Examination of Deceptive Counterfeiting Activities in Electronic Markets*. Doctoral dissertation, University of California, Irvine. [Repository](https://escholarship.org/uc/item/5v85s1fm).
[5] Pavlou, P. A. (2003). *Consumer Acceptance of Electronic Commerce*. International Journal of Electronic Commerce, 7(3), 101-134. [Publisher record and abstract](https://www.tandfonline.com/doi/abs/10.1080/10864415.2003.11044275).
[6] Gefen, D., Karahanna, E., and Straub, D. W. (2003). *Trust and TAM in Online Shopping*. MIS Quarterly, 27(1), 51-90. [Journal record and abstract](https://aisel.aisnet.org/misq/vol27/iss1/4/).
[7] Pontiki, M., et al. (2014). *SemEval-2014 Task 4. Aspect Based Sentiment Analysis*. Proceedings of SemEval 2014, 27-35. [Paper](https://aclanthology.org/S14-2004/).
[8] He, S., Hollenbeck, B., Overgoor, G., Proserpio, D., and Tosyali, A. (2022). *Detecting fake-review buyers using network structure*. PNAS, 119(47), e2211932119. [Author manuscript posted in 2024](https://arxiv.org/abs/2410.17507).
[9] Ratner, A., et al. (2017). *Rapid Training Data Creation with Weak Supervision*. Proceedings of the VLDB Endowment, 11(3), 269-282. [Snorkel manuscript](https://arxiv.org/abs/1711.10160).
[10] Guo, C., Pleiss, G., Sun, Y., and Weinberger, K. Q. (2017). *On Calibration of Modern Neural Networks*. Proceedings of ICML, 70, 1321-1330. [Paper](https://proceedings.mlr.press/v70/guo17a.html).
[11] Amazon India. (2023). *Amazon.in improves customer reviews experience with generative AI*. [Announcement](https://press.aboutamazon.com/in/2023/12/amazon-in-improves-customer-reviews-experience-with-generative-ai).
[12] Amazon India. (n.d.). *Amazon announces the launch of Rufus in India*. Accessed 31 October 2026. [Product description](https://www.aboutamazon.in/news/retail/rufus-ai-shopping-assistant-launch-in-india).
[13] Amazon India. (n.d.). *Transparency*. Accessed 31 October 2026. [Programme description](https://sell.amazon.in/brand-registry/transparency).
[14] Flipkart. (2026). *With Open Box Delivery, Flipkart Safeguards Customer Interests and Fosters Trust*. [Service description](https://stories.flipkart.com/open-box-delivery-flipkart-customer-trust).
[15] Prabhavalkar, N. (n.d.). *Indian Products on Amazon*. [Dataset](https://www.kaggle.com/datasets/nehaprabhavalkar/indian-products-on-amazon).
[16] McAuley Lab. (n.d.). *Amazon Reviews 2023*. [Dataset](https://huggingface.co/datasets/McAuley-Lab/Amazon-Reviews-2023).
[17] Karkavelraj Aj. (n.d.). *Amazon Sales Dataset*. [Dataset](https://www.kaggle.com/datasets/karkavelrajaj/amazon-sales-dataset).
[18] SC4025 project research. (2026). *Methodology and Research Development* and *Synthetic Data Methodology*, with the saved low-star, context, sample-size and synthetic-validation outputs. These internal records document the observations and prototype assumptions reported here.
