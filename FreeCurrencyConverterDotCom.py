import requests
from requests.exceptions import RequestException

from core.base.model.Intent import Intent
from core.base.model.AliceSkill import AliceSkill
from core.dialog.model.DialogSession import DialogSession
from core.util.Decorators import AnyExcept, Online, IntentHandler


class FreeCurrencyConverterDotCom(AliceSkill):
	"""
	Author: Psychokiller1888
	Description: Let's you convert world currencies
	"""

	def __init__(self):
		super().__init__()
		self._apiKey = self.getConfig('apiKey')


	@IntentHandler('ConvertCurrency')
	@IntentHandler('AnswerCurrency')
	@AnyExcept(exceptions=(RequestException, KeyError), text='noServer', printStack=True)
	@Online
	def convertCurrencyIntent(self, session: DialogSession):
		self._apiKey = self.getConfig('apiKey')
		amount = session.slotValue('Amount', defaultValue=1)
		toCurrency = session.slotValue('ToCurrency', defaultValue=session.customData.get('toCurrency',self.ConfigManager.getAliceConfigByName('baseCurrency')))
		toCurrencyRAW = session.slots.get('ToCurrency', session.customData.get('toCurrencyRAW',toCurrency))

		fromCurrency = session.slotValue('FromCurrency', defaultValue=session.slotValue('Currency'))
		fromCurrencyRAW = session.slots.get('FromCurrency', fromCurrency)

		if not fromCurrency:
			self.continueDialog(
				sessionId=session.sessionId,
				intentFilter=[Intent('AnswerCurrency')],
				text=self.TalkManager.randomTalk(skill=self.name, talk='fromWhatCurrency'),
				customData={
					'skill'    : self.name,
					'amount'    : amount,
					'toCurrency': toCurrency,
					'toCurrencyRAW': toCurrencyRAW
				}
			)
			return

		if not self._apiKey:
			self.logWarning(msg="please create a api key at https://www.currencyconverterapi.com/ and add it to the skill config")
			self.endDialog(session.sessionId, text=self.randomTalk('noApiKey'))
			return

		convString = f'{fromCurrency}_{toCurrency}'

		url = f'https://free.currconv.com/api/v7/convert?q={convString}&compact=ultra&apiKey={self._apiKey}'

		response = requests.get(url=url)
		if not response:
			raise Exception(response.json()['error'])

		data = response.json()

		if convString not in data:
			self.endDialog(session.sessionId, text=self.randomTalk('noConversionExists').format(fromCurrencyRAW, toCurrencyRAW))
			return

		conversion = data[convString]
		converted = round(float(amount) * float(conversion), 2)

		self.endDialog(session.sessionId, text=self.randomTalk('answer').format(amount, fromCurrencyRAW, converted, toCurrencyRAW))
