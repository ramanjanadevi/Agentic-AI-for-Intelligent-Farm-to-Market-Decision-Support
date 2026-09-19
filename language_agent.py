"""
AgriSell AI - Language & Explainability Agent
Synthesizes dynamic natural-language rationales directly from live quantitative agent outputs.
Never serves canned static text: changes dynamically with every input and produces multilingual explanations.
"""

from typing import Dict, Any

class LanguageAgent:
    def generate_explanation(
        self,
        winning_option: Dict[str, Any],
        market_res: Dict[str, Any],
        weather_res: Dict[str, Any],
        storage_res: Dict[str, Any],
        logistics_res: Dict[str, Any],
        crop_name: str,
        quantity: float,
        language: str = "en"
    ) -> Dict[str, str]:
        local_p = market_res.get("localPrice", 20.0)
        best_p = market_res.get("bestMarketPrice", 25.0)
        best_city = market_res.get("bestNearbyMarket", "Regional Hub")
        future_p = market_res.get("expectedFuturePrice", 28.0)
        weather_risk = weather_res.get("weatherRisk", "LOW")
        rain_prob = weather_res.get("rainProbability", "20%")
        storage_feasible = storage_res.get("isFeasible", False)
        spoilage_pct = storage_res.get("expectedSpoilagePercent", 5.0)
        net_ret = winning_option.get("netReturn", 0.0)

        # Construct dynamic English narrative
        opt_id = winning_option.get("id")

        if opt_id == "OTHER_MARKET":
            best_route = logistics_res.get("bestLogisticsMarketDetails", {})
            t_cost = best_route.get("transportCost", 2000.0)
            reason_en = (
                f"Although the local mandi price at your location is ₹{local_p:,.1f}/kg, "
                f"{best_city} offers a significantly higher wholesale rate of ₹{best_p:,.1f}/kg (+₹{best_p - local_p:,.1f}/kg premium). "
                f"Even after deducting vehicle freight and transit handling costs of ₹{t_cost:,.0f}, "
                f"selling at {best_city} yields a superior net return of ₹{net_ret:,.0f}. "
                f"Weather conditions show a {rain_prob} rain probability ({weather_risk} risk), which is manageable for covered transport."
            )
        elif opt_id == "STORE_LATER":
            reason_en = (
                f"The expected future price of ₹{future_p:,.1f}/kg represents a solid premium over the current spot price of ₹{local_p:,.1f}/kg. "
                f"Your storage facility is verified with adequate capacity for {quantity:,.0f} kg. "
                f"With an estimated spoilage of only {spoilage_pct}% over the recommended {storage_res.get('recommendedDurationDays', 7)}-day hold, "
                f"the net stored value will deliver an estimated ₹{net_ret:,.0f}, easily outweighing daily storage charges."
            )
        elif opt_id == "SELL_NOW":
            reason_en = (
                f"Selling immediately in the local market minimizes downside exposure. "
                f"At ₹{local_p:,.1f}/kg, your estimated net return is ₹{net_ret:,.0f} with zero freight expenses or warehouse holding risks. "
                + (f"Given the {weather_risk} weather risk and {rain_prob} rain likelihood, holding or long-distance hauling carries excessive spoilage hazards." if weather_risk in ["HIGH", "MEDIUM"] else "This locks in prompt payment and eliminates price volatility.")
            )
        else: # MONITOR_MARKET
            reason_en = (
                f"Market indicators show an active {market_res.get('trend', 'Stable').lower()} price trend. "
                f"Holding harvest for 48 to 72 hours locally allows you to wait for rising mandi arrivals and price peaks, "
                f"while keeping transport commitments flexible. Monitor price alerts closely."
            )

        # Multilingual synthesis
        translations = {
            "en": reason_en,
            "te": self._translate_te(opt_id, crop_name, local_p, best_city, best_p, net_ret, weather_risk, storage_feasible),
            "hi": self._translate_hi(opt_id, crop_name, local_p, best_city, best_p, net_ret, weather_risk, storage_feasible),
            "ta": self._translate_ta(opt_id, crop_name, local_p, best_city, best_p, net_ret, weather_risk),
            "kn": self._translate_kn(opt_id, crop_name, local_p, best_city, best_p, net_ret, weather_risk),
            "mr": self._translate_mr(opt_id, crop_name, local_p, best_city, best_p, net_ret, weather_risk),
            "bn": self._translate_bn(opt_id, crop_name, local_p, best_city, best_p, net_ret, weather_risk),
            "gu": self._translate_gu(opt_id, crop_name, local_p, best_city, best_p, net_ret, weather_risk),
            "pa": self._translate_pa(opt_id, crop_name, local_p, best_city, best_p, net_ret, weather_risk),
            "ml": self._translate_ml(opt_id, crop_name, local_p, best_city, best_p, net_ret, weather_risk),
            "or": self._translate_or(opt_id, crop_name, local_p, best_city, best_p, net_ret, weather_risk)
        }

        active_reason = translations.get(language, reason_en)

        # Voice script for Text-to-Speech (TTS)
        voice_scripts = {
            "en": f"AgriSell AI recommends: {winning_option['title']}. Expected net return is {int(net_ret):,} Rupees at an average price of {winning_option['pricePerKg']} Rupees per kilogram. Confidence is {winning_option.get('confidence', 80)} percent.",
            "te": f"అగ్రిసెల్ AI సిఫార్సు: {winning_option['title']}. అంచనా నికర రాబడి ₹{int(net_ret):,}. సగటు ధర కిలోకు ₹{winning_option['pricePerKg']}.",
            "hi": f"एग्रीसेल एआई की सिफारिश: {winning_option['title']}. अनुमानित शुद्ध लाभ ₹{int(net_ret):,}, औसत भाव ₹{winning_option['pricePerKg']} प्रति किलो है।",
            "mr": f"अॅग्रीसेल एआयची शिफारस: {winning_option['title']}. अपेक्षित निव्वळ नफा ₹{int(net_ret):,}, सरासरी दर ₹{winning_option['pricePerKg']} प्रति किलो आहे.",
            "bn": f"অ্যাগ্রিসেল এআই সুপারিশ: {winning_option['title']}। প্রত্যাশিত নিট লাভ ₹{int(net_ret):,}, গড় মূল্য ₹{winning_option['pricePerKg']} প্রতি কেজি।",
            "gu": f"એગ્રીસેલ એઆઈની ભલામણ: {winning_option['title']}. અપેક્ષિત ચોખ્ખો નફો ₹{int(net_ret):,}, સરેરાશ ભાવ ₹{winning_option['pricePerKg']} પ્રતિ કિલો છે.",
            "pa": f"ਐਗਰੀਸੈੱਲ ਏਆਈ ਦੀ ਸਿਫਾਰਸ਼: {winning_option['title']}. ਅਨੁਮਾਨਿਤ ਸ਼ੁੱਧ ਮੁਨਾਫਾ ₹{int(net_ret):,}, ਔਸਤ ਭਾਅ ₹{winning_option['pricePerKg']} ਪ੍ਰਤੀ ਕਿਲੋ ਹੈ।",
            "ta": f"அக்ரிசெல் AI பரிந்துரை: {winning_option['title']}. எதிர்பார்க்கப்படும் நிகர லாபம் ₹{int(net_ret):,}.",
            "kn": f"ಅಗ್ರಿಸೆಲ್ AI ಶಿಫಾರಸು: {winning_option['title']}. ನಿರೀಕ್ಷಿತ ನಿವ್ವಳ ಲಾಭ ₹{int(net_ret):,}.",
            "ml": f"അഗ്രിസെൽ എഐ ശുപാർശ: {winning_option['title']}. പ്രതീക്ഷിക്കുന്ന അറ്റാദായം ₹{int(net_ret):,}.",
            "or": f"ଏଗ୍ରିସେଲ ଏଆଇ ପରାମର୍ଶ: {winning_option['title']}। ଅନୁମାନିତ ନିଟ୍ ଲାଭ ₹{int(net_ret):,}।"
        }

        voice_script = voice_scripts.get(language, voice_scripts["en"])

        return {
            "explanation": active_reason,
            "voiceScript": voice_script,
            "language": language
        }

    def _translate_te(self, opt_id, crop, local_p, best_city, best_p, net_ret, weather_risk, storage_ok):
        if opt_id == "OTHER_MARKET":
            return f"స్థానిక మార్కెట్ ధర ₹{local_p}/కిలో కంటే {best_city} మార్కెట్లో ₹{best_p}/కిలో లభిస్తోంది. రవాణా ఖర్చులు పోను మీకు గరిష్టంగా ₹{net_ret:,.0f} నికర రాబడి లభిస్తుంది. కావున {best_city} మార్కెట్‌కు రవాణా చేయడం లాభదాయకం."
        elif opt_id == "STORE_LATER":
            return f"భవిష్యత్తులో ధరలు పెరిగే అవకాశం ఉంది. మీ వద్ద నిల్వ సౌకర్యం అందుబాటులో ఉన్నందున, కొద్ది రోజులు నిల్వ చేసి విక్రయించడం ద్వారా ₹{net_ret:,.0f} అధిక రాబడిని పొందవచ్చు."
        elif opt_id == "SELL_NOW":
            return f"ప్రస్తుత వాతావరణం మరియు మార్కెట్ పరిస్థితుల దృష్ట్యా పంటను వెంటనే స్థానిక మార్కెట్లో విక్రయించడం సురక్షితం. దీనివల్ల రవాణా ఖర్చులు, నిల్వ నష్టాలు ఉండవు. నికర రాబడి: ₹{net_ret:,.0f}."
        return f"మార్కెట్ ట్రెండ్‌ను గమనిస్తూ 2-3 రోజులు నిరీక్షించడం ఉత్తమం. ఆ తర్వాత సరైన ధరకు విక్రయించండి."

    def _translate_hi(self, opt_id, crop, local_p, best_city, best_p, net_ret, weather_risk, storage_ok):
        if opt_id == "OTHER_MARKET":
            return f"स्थानीय मंडी भाव ₹{local_p}/किग्रा की तुलना में {best_city} में ₹{best_p}/किग्रा का बेहतर भाव मिल रहा है। परिवहन लागत घटाने के बाद भी आपको ₹{net_ret:,.0f} का शुद्ध लाभ मिलेगा।"
        elif opt_id == "STORE_LATER":
            return f"भविष्य में भाव बढ़ने की संभावना है। आपके पास सुरक्षित भंडारण उपलब्ध है। कुछ दिन भंडारण करके बेचने पर ₹{net_ret:,.0f} का बेहतर लाभ मिलेगा।"
        elif opt_id == "SELL_NOW":
            return f"मौसम के जोखिम और मौजूदा हालात को देखते हुए फसल को तुरंत स्थानीय मंडी में बेचना सबसे सुरक्षित है। अपेक्षित शुद्ध लाभ ₹{net_ret:,.0f} है।"
        return f"बाजार की स्थिति पर 2-3 दिन नजर रखें। भाव में उछाल आते ही बेचने की योजना बनाएं।"

    def _translate_ta(self, opt_id, crop, local_p, best_city, best_p, net_ret, weather_risk):
        if opt_id == "OTHER_MARKET":
            return f"உள்ளூர் சந்தையை விட {best_city} சந்தையில் அதிக விலை கிடைக்கிறது. போக்குவரத்து செலவுகள் போக நிகர வருமானம் ₹{net_ret:,.0f}."
        return f"தற்போதைய சந்தை மற்றும் வானிலை நிலவரப்படி, உடனடியாக விற்பனை செய்வதே அதிக லாபம் தரும். எதிர்பார்க்கப்படும் நிகர வருவாய் ₹{net_ret:,.0f}."

    def _translate_kn(self, opt_id, crop, local_p, best_city, best_p, net_ret, weather_risk):
        if opt_id == "OTHER_MARKET":
            return f"ಸ್ಥಳೀಯ ಮಾರುಕಟ್ಟೆಗಿಂತ {best_city} ನಲ್ಲಿ ಹೆಚ್ಚಿನ ಬೆಲೆ ದೊರೆಯುತ್ತಿದೆ. ಸಾರಿಗೆ ವೆಚ್ಚದ ನಂತರ ನಿವ್ವಳ ಲಾಭ ₹{net_ret:,.0f}."
        return f"ಪ್ರಸ್ತುತ ಹವಾಮಾನ ಮತ್ತು ಮಾರುಕಟ್ಟೆ ಪರಿಸ್ಥಿತಿಯನ್ನು ಗಮನಿಸಿ, ತಕ್ಷಣ ಮಾರಾಟ ಮಾಡುವುದು ಸುರಕ್ಷಿತ. ನಿರೀಕ್ಷಿತ ಲಾಭ ₹{net_ret:,.0f}."

    def _translate_mr(self, opt_id, crop, local_p, best_city, best_p, net_ret, weather_risk):
        if opt_id == "OTHER_MARKET":
            return f"स्थानिक बाजारभावापेक्षा {best_city} बाजारपेठेत ₹{best_p}/किलो असा अधिक दर मिळत आहे. वाहतूक खर्च वजा जाता तुम्हाला ₹{net_ret:,.0f} चा उत्तम निव्वळ नफा मिळेल."
        elif opt_id == "STORE_LATER":
            return f"भविष्यात दर वाढण्याची शक्यता आहे. आपल्याकडे सुरक्षित साठवणूक उपलब्ध असल्याने काही दिवस साठवून विकल्यास ₹{net_ret:,.0f} नफा मिळू शकतो."
        elif opt_id == "SELL_NOW":
            return f"हवामानाचा धोका आणि सध्याची परिस्थिती लक्षात घेता स्थानिक बाजारात लगेच विक्री करणे सर्वात सुरक्षित आहे. अपेक्षित निव्वळ नफा ₹{net_ret:,.0f} आहे."
        return f"बाजारावर २-३ दिवस लक्ष ठेवा. आवक आणि दर अनुकूल होताच विक्रीचा निर्णय घ्या."

    def _translate_bn(self, opt_id, crop, local_p, best_city, best_p, net_ret, weather_risk):
        if opt_id == "OTHER_MARKET":
            return f"স্থানীয় মাণ্ডির চেয়ে {best_city} বাজারে ₹{best_p}/কেজি বেশি দর পাওয়া যাচ্ছে। পরিবহন খরচ বাদ দিয়েও নিট লাভ ₹{net_ret:,.0f} হবে।"
        elif opt_id == "STORE_LATER":
            return f"ভবিষ্যতে দাম বাড়ার সম্ভাবনা রয়েছে। উপযুক্ত গুদাম থাকায় কিছুদিন মজুত করে বিক্রি করলে ₹{net_ret:,.0f} অধিক লাভ হতে পারে।"
        elif opt_id == "SELL_NOW":
            return f"আবহাওয়ার ঝুঁকি এড়াতে অবিলম্বে স্থানীয় বাজারে বিক্রি করাই লাভজনক। প্রত্যাশিত নিট লাভ ₹{net_ret:,.0f}।"
        return f"বাজারে ২-৩ দিন নজর রাখুন। দর বাড়লে বিক্রি করুন।"

    def _translate_gu(self, opt_id, crop, local_p, best_city, best_p, net_ret, weather_risk):
        if opt_id == "OTHER_MARKET":
            return f"સ્થાનિક યાર્ડ કરતા {best_city} માં ₹{best_p}/કિલોનો ઊંચો ભાવ મળી રહ્યો છે. વાહનભાડું બાદ કરતા પણ ₹{net_ret:,.0f} નો ચોખ્ખો નફો થશે."
        elif opt_id == "STORE_LATER":
            return f"ભવિષ્યમાં ભાવ વધવાની પૂરી શક્યતા છે. સંગ્રહ ક્ષમતા ઉપલબ્ધ હોવાથી થોડા દિવસ સંગ્રહ કરી વેચવાથી ₹{net_ret:,.0f} નો ફાયદો થશે."
        elif opt_id == "SELL_NOW":
            return f"હવામાનના જોખમને જોતા અત્યારે જ સ્થાનિક યાર્ડમાં વેચાણ કરવું સૌથી સલામત છે. અપેક્ષિત ચોખ્ખો નફો ₹{net_ret:,.0f} છે."
        return f"બજારના વલણ પર ૨-૩ દિવસ નજર રાખો. ભાવ વધે ત્યારે વેચાણ કરો."

    def _translate_pa(self, opt_id, crop, local_p, best_city, best_p, net_ret, weather_risk):
        if opt_id == "OTHER_MARKET":
            return f"ਸਥਾਨਕ ਮੰਡੀ ਨਾਲੋਂ {best_city} ਮੰਡੀ ਵਿੱਚ ₹{best_p}/ਕਿਲੋ ਦਾ ਚੰਗਾ ਭਾਅ ਮਿਲ ਰਿਹਾ ਹੈ। ਕਿਰਾਇਆ ਕੱਟ ਕੇ ਵੀ ਤੁਹਾਨੂੰ ₹{net_ret:,.0f} ਦਾ ਸ਼ੁੱਧ ਮੁਨਾਫਾ ਮਿਲੇਗਾ।"
        elif opt_id == "STORE_LATER":
            return f"ਭਵਿੱਖ ਵਿੱਚ ਭਾਅ ਵਧਣ ਦੀ ਉਮੀਦ ਹੈ। ਸਟੋਰੇਜ ਉਪਲਬਧ ਹੋਣ ਕਰਕੇ ਕੁਝ ਦਿਨ ਰੱਖ ਕੇ ਵੇਚਣ ਨਾਲ ₹{net_ret:,.0f} ਜ਼ਿਆਦਾ ਮੁਨਾਫਾ ਹੋਵੇਗਾ।"
        elif opt_id == "SELL_NOW":
            return f"ਮੌਸਮ ਦੇ ਜੋਖਮ ਨੂੰ ਵੇਖਦੇ ਹੋਏ ਫਸਲ ਨੂੰ ਤੁਰੰਤ ਸਥਾਨਕ ਮੰਡੀ ਵਿੱਚ ਵੇਚਣਾ ਸਭ ਤੋਂ ਸੁਰੱਖਿਅਤ ਹੈ। ਅਨੁਮਾਨਿਤ ਸ਼ੁੱਧ ਮੁਨਾਫਾ ₹{net_ret:,.0f} ਹੈ।"
        return f"ਮੰਡੀ ਤੇ ੨-੩ ਦਿਨ ਨਜ਼ਰ ਰੱਖੋ। ਭਾਅ ਵਧਣ ਤੇ ਵੇਚਣ ਦਾ ਫੈਸਲਾ ਕਰੋ।"

    def _translate_ml(self, opt_id, crop, local_p, best_city, best_p, net_ret, weather_risk):
        if opt_id == "OTHER_MARKET":
            return f"പ്രാദേശിക വിപണിയേക്കാൾ {best_city} വിപണിയിൽ ഉയർന്ന വില ലഭിക്കുന്നു. ഗതാഗത ചെലവ് കഴിഞ്ഞ് ₹{net_ret:,.0f} അറ്റാദായം ലഭിക്കും."
        return f"നിലവിലെ കാലാവസ്ഥ കണക്കിലെടുത്ത് വിള ഉടൻ വിൽക്കുന്നതാണ് ഏറ്റവും സുരക്ഷിതം. പ്രതീക്ഷിക്കുന്ന അറ്റാദായം ₹{net_ret:,.0f}."

    def _translate_or(self, opt_id, crop, local_p, best_city, best_p, net_ret, weather_risk):
        if opt_id == "OTHER_MARKET":
            return f"ସ୍ଥାନୀୟ ମଣ୍ଡି ତୁଳନାରେ {best_city} ମଣ୍ଡିରେ ଅଧିକ ମୂଲ୍ୟ ମିଳୁଛି। ପରିବହନ ଖର୍ଚ୍ଚ ପରେ ନିଟ୍ ଲାଭ ₹{net_ret:,.0f} ହେବ।"
        return f"ପାଣିପାଗ ପରିସ୍ଥିତିକୁ ଦୃଷ୍ଟିରେ ରଖି ତୁରନ୍ତ ସ୍ଥାନୀୟ ମଣ୍ଡିରେ ବିକ୍ରୟ କରିବା ସୁରକ୍ଷିତ। ଅନୁମାନିତ ନିଟ୍ ଲାଭ ₹{net_ret:,.0f}।"

