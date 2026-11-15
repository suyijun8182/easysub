// Canonical names come from backend/app/seed.py and the preview seed.json.
// Match system records only; names in the database and sync wire stay untouched.
const payments = {
  '信用卡 / Credit Card':['信用卡','Credit Card','Кредитная карта'],
  '借记卡 / Debit Card':['借记卡','Debit Card','Дебетовая карта'],
  'Apple Pay':['Apple Pay','Apple Pay','Apple Pay'],
  'Google Pay':['Google Pay','Google Pay','Google Pay'],
  '支付宝 / Alipay':['支付宝','Alipay','Alipay'],
  '微信支付 / WeChat Pay':['微信支付','WeChat Pay','WeChat Pay'],
  'PayPal':['PayPal','PayPal','PayPal'],
  '银行转账 / Bank Transfer':['银行转账','Bank Transfer','Банковский перевод'],
  '加密货币 / Crypto':['加密货币','Crypto','Криптовалюта']
}
const language = locale => ({zh:0,en:1,ru:2}[locale] ?? 1)
export const paymentName = (row,locale) => row?.is_system ? payments[row.name]?.[language(locale)] || row.name : row?.name || ''
