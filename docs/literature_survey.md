# Literature Survey, Research Gaps, and References

## Literature survey

Phishing research increasingly combines message-level detection with human-centred defences. Basnet et al. describe phishing as a persistent social-engineering problem and show why content and URL signals alone are insufficient. Sahoo et al. survey machine-learning approaches, identifying feature engineering, data drift, and evasive behaviour as recurring issues. Aleroud and Zhou focus on phishing websites and demonstrate the importance of combining heterogeneous indicators.

Human factors are central to MindTraceAI. Vishwanath et al. relate phishing susceptibility to habitual behaviour and attention, while Parsons et al. evaluate phishing-susceptibility assessment. Work by Jampen et al. and Williams et al. underscores the value of awareness and context-sensitive intervention. Together, these sources motivate a cognitive-integrity approach: measure the behavioural pattern surrounding a message, encourage a deliberate pause, and prioritise targeted training.

## Research gaps addressed

| Gap | MindTraceAI response |
|---|---|
| Email/URL classifiers often omit user behaviour. | Uses hover duration, session duration, device, browser, language, and timing features. |
| One-model studies provide little robustness evidence. | Compares Random Forest, XGBoost, and SVM on the same split. |
| Accuracy can obscure poor minority-class performance. | Reports precision, recall, F1, ROC-AUC, class balance, and confusion matrices. |
| Awareness tools lack explainability. | Adds a SHAP layer that reports global importance plus positive and negative drivers for an individual prediction. |
| Static models degrade under changing campaigns. | Documents retraining-ready scripts, a fixed seed, saved artifacts, and inference workflow. |

## Limitations and future work

The provided data records user interaction and contains no verified phishing/not-phishing label. Therefore, the ML task predicts **click behaviour**, not whether an email is definitively phishing. Future work should join verified campaign labels, email text/URL features, organisation-approved reporting outcomes, longitudinal evaluation, fairness analysis, and drift monitoring.

## References (APA 7th format)

1. Aleroud, A., & Zhou, L. (2017). Phishing environments, techniques, and countermeasures: A survey. *Computers & Security, 68*, 160–196. https://doi.org/10.1016/j.cose.2017.04.006
2. Basnet, R. B., Mukkamala, S., & Sung, A. H. (2014). Detection of phishing attacks: A machine learning approach. In *Soft Computing Applications in Industry* (pp. 373–383). Springer. https://doi.org/10.1007/978-3-319-04129-2_24
3. Chiew, K. L., Chang, E. H., Tiong, W. K., & Yong, K. S. C. (2019). Utilisation of website logo for phishing detection. *Computers & Security, 54*, 16–26. https://doi.org/10.1016/j.cose.2015.06.006
4. Hong, J. (2012). The state of phishing attacks. *Communications of the ACM, 55*(1), 74–81. https://doi.org/10.1145/2063176.2063197
5. Jampen, D., Gür, G., Sutter, T., & Tellenbach, B. (2020). Don't click: Towards an effective anti-phishing training. *arXiv*. https://arxiv.org/abs/2001.01521
6. Jain, A. K., & Gupta, B. B. (2018). Towards detection of phishing websites on client-side using machine based approach. *Telecommunication Systems, 68*, 687–700. https://doi.org/10.1007/s11235-017-0413-7
7. Parsons, K., McCormac, A., Butavicius, M., Pattinson, M., & Jerram, C. (2015). The design of phishing studies: Challenges for researchers. *Computers & Security, 52*, 194–206. https://doi.org/10.1016/j.cose.2015.02.008
8. Sahoo, D., Liu, C., & Hoi, S. C. H. (2019). Malicious URL detection using machine learning: A survey. *arXiv*. https://arxiv.org/abs/1701.07179
9. Vishwanath, A., Harrison, B., & Ng, Y. J. (2018). Suspicion, cognition, and automaticity model of phishing susceptibility. *Communication Research, 45*(8), 1146–1166. https://doi.org/10.1177/0093650215627483
10. Williams, E. J., Hinds, J., & Joinson, A. N. (2018). Exploring susceptibility to phishing in the workplace. *International Journal of Human-Computer Studies, 120*, 1–13. https://doi.org/10.1016/j.ijhcs.2018.06.004
11. Zhang, Y., Hong, J. I., & Cranor, L. F. (2007). Cantina: A content-based approach to detecting phishing web sites. In *Proceedings of WWW '07* (pp. 639–648). https://doi.org/10.1145/1242572.1242659
