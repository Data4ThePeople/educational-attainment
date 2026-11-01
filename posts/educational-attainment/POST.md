---
title:
subtitle:
slug: educational-attainment
date:
section: Data 4 Thought
hero: images/educational-attainment-hero-1680x1080.png
hero_alt:
meta_title:
description:
keywords:
schema_type: article
drop_cap: true
heading_spacer: 20px
caption_spacer: 20px
dividers: false
---

# Title

Last Thursday, after a delay of about six weeks the Census Bureau finally released the results of its 1-year American Community Survey (ACS) for 2025. Over the weekend, we rolled up our sleeves and dug in, excited to see what new learnings we could find on America’s larger communities (the 1-year ACS covers only areas with 65,000 or more people).

We started with a topic we haven’t yet explored – educational attainment. We created a visualization to see how educational attainment changed between 2015 and 2025 – by state, county, and metro/micro area. Find where you live below.

<iframe src="https://data4thepeople.github.io/educational-attainment/dist/?v=20261101a#embed=1" width="100%" height="900" loading="lazy" style="border:0" title="Educational attainment and pay: interactive map by state, county and metro or micro area, 2015 to 2025"></iframe>
::: spacer 20px

On its own, the educational attainment data is quite encouraging. The share of America with more education is not only rising on the aggregate but is rising just about everywhere. The next chart shows how much education rose in each metro and micro area over the past decade, and the percentage of areas where the rise was statistically significant.

![Dot chart of 391 metro and micro areas showing the change from 2015 to 2025 in the share of adults 25 and over at four levels of education. Most dots sit to the right of zero at every level. The share of areas where the rise passed the Census Bureau's test was 26% for high school or more, 54% for some college or more, 78% for a bachelor's degree or more and 64% for a graduate or professional degree.](images/01-edu-rise-metros.png)
*Each dot is one of 391 metro and micro areas. Dark blue dots had a rise large enough to pass the Census Bureau's test at 90% confidence.*

So that’s fantastic. Story over?

Not so fast. This got me thinking about how people (including myself) analyze pay data. I’ve spent a lot of time poking around in pay data at the county level and have compared one period to another often in the past.

But if educational attainment is changing so dramatically, is it appropriate to draw any conclusions from the raw data without adjusting it for variables like educational attainment? Probably not. To explain why, we need to talk about a concept the corporate finance world calls “mix.”

## A mixed-up coffee shop

Let’s say you are hired to do revenue analysis for your friend’s coffee shop. Luckily, the shop only has two products – drip coffee and a triple-whip mocha pumpkin spiced matcha latte (TWMPSML for short).

Here’s the info you need to do the middle school math that corporate finance professionals do each day (I used to be one of them so I can poke fun at the profession).

Last year, the shop sold 5,000 coffees at $2 each and 6,000 TWMPSMLs at $12 each. This year the shop sold 3,000 coffees at $2.50 each and 8,000 TWMPSMLs at $12.50 each.

Overall, the shop’s revenue went from $82,000 to $107,500, an increase of $25,500 or 31%.

What’s the revenue impact from volume? That’s easy. It’s zero since in both years the shop sold 11,000 drinks.

Now what about price? To calculate that, you must apply only the change in pricing to the base year’s volume. Both coffee and TWMPSML took a $0.50 price increase. Applying that to last year’s volume tells us that pricing alone explains just $5,500 of the revenue increase.

So, what explains the remaining $20,000 increase? MIX. The shop sold far more of the expensive items and fewer of the cheaper items. The chart below shows all three pieces.

![Bridge chart of a coffee shop's revenue. Last year's revenue of $82,000 rises by $0 from volume, $5,500 from price and $20,000 from mix to reach this year's revenue of $107,500.](images/02-coffee-bridge.png)
*Made-up numbers for the coffee shop example.*

Notice this provides the shop with different insight than just telling your friend, “Your revenue rose 31%” and letting them guess the reason why. This pinpoints that her success was due to the popularity of the TWMPSML.

I offer this illustration to help understand the problem with pay analysis over time when there are major underlying demographic (i.e., mix) changes in a community. Increased pay in a community could be driven by better educational attainment (i.e., more college grads) rather than companies increasing pay within a given level of educational attainment.

And so, I added this to the visualization. Just switch the topic from Education to Pay and you can see how much of the increase in pay comes from higher pay within each education group and how much comes from the change in education mix. The following chart shows the summary of this pay and mix analysis for the nation.

![Bar chart of the yearly change in U.S. median pay after inflation, 2015 to 2025, in 2025 dollars. Less than high school: $29,056 to $34,670, 1.78% a year. High school: $39,528 to $41,466, 0.48%. Some college: $46,851 to $50,003, 0.65%. Bachelor's: $69,410 to $71,709, 0.33%. Graduate: $91,701 to $91,554, flat. All workers: $50,235 to $55,391, 0.98%. Pay index: $52,033 to $57,469, 1.00%, of which 0.49 points from pay within groups and 0.51 from the education mix.](images/03-pay-mix-nation.png)
*Pay is median earnings of people 25 and over who had earnings, in 2025 dollars. Yearly change is the average yearly growth rate over the 10 years, with compounding. The pay index weights each group's median pay by that group's share of all adults 25 and over.*

From 2015 to 2025, median pay for all U.S. workers 25 and over rose 0.98% a year after inflation. Pay within each education group tells a different story. Median pay rose 0.33% a year for workers with a bachelor's degree and was flat for workers with a graduate or professional degree (down 0.02% a year, a change too small to pass the Census Bureau's test). Only workers without a high school diploma saw their median pay rise faster than all workers, at 1.78% a year.

Over the same years, the education mix shifted. The share of adults 25 and over with a bachelor's degree or more rose from 30.6% to 37.4%. The share without a high school diploma fell from 12.9% to 9.4%. More adults are now in the groups with higher pay.

The pay index in the map splits the change in pay into two parts. It weights each group's median pay by that group's share of adults 25 and over. From 2015 to 2025 the index rose 1.00% a year, close to the 0.98% yearly rise in median pay. With the education mix held at 2015 shares, the index would have risen 0.49% a year. The other 0.51 points a year are pay index growth from the change in education mix. In other words, about half of the rise in the pay index lines up with higher pay within education groups, and about half lines up with the shift toward more education.

The next chart shows the same split for each of the 391 metro and micro areas.

![Scatter plot of 391 metro and micro areas. The horizontal axis is pay index growth from pay within education groups, in percent a year, from about -2% to +3%. The vertical axis is growth from the change in education mix, in points a year, from about -0.3 to +1.1. Both parts rose in 317 areas. Pay within groups fell while the education mix part rose in 62 areas, including New York and Houston. The education mix part fell in 12 areas.](images/04-pay-mix-metros.png)
*Each dot is one metro or micro area with comparable 2015 and 2025 boundaries. The two parts add up to the yearly change in the pay index. Dots above the dashed line have a larger education mix part than pay part.*

The education mix part is above zero in 379 of the 391 areas, and in 336 of them (86%) it is between 0.1 and 0.7 points a year. The part from pay within education groups is more spread out, from about −2% to +3% a year. In 62 areas, pay within education groups fell while the education mix part rose. That includes New York, where the pay part was −0.20% a year and the mix part was +0.65 points, and Houston, at −0.53% and +0.54 points. In 159 areas, the education mix part was larger than the pay part.
