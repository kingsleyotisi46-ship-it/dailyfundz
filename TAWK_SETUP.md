# Tawk.to Setup Instructions

## Get Your Tawk.to Widget Code

1. **Sign up / Login to Tawk.to**
   - Go to: https://www.tawk.to/
   - Create a free account or login

2. **Create a Property**
   - After login, create a new property for your website
   - Enter: dailyfundzboost.trade

3. **Get Widget Code**
   - Go to: Administration > Channels > Chat Widget
   - Copy your unique property ID and widget ID
   - They look like: `https://embed.tawk.to/PROPERTY_ID/WIDGET_ID`

4. **Update base.html**
   - Open: templates/base.html
   - Find the Tawk.to script section (around line 195)
   - Replace:
     ```
     s1.src='https://embed.tawk.to/YOUR_PROPERTY_ID/YOUR_WIDGET_ID';
     ```
   - With your actual IDs from Tawk.to dashboard

## Features Available in Tawk.to

✅ Live chat widget (replaces WhatsApp float button)
✅ Chat history & transcripts
✅ Mobile apps for iOS & Android
✅ Visitor monitoring
✅ Canned responses / Quick replies
✅ File sharing
✅ Integrations (Slack, etc.)
✅ Completely FREE!

## Customization

In Tawk.to dashboard, you can customize:
- Widget color (match your brand: #FF6B00)
- Widget position (bottom right/left)
- Online/offline messages
- Pre-chat form
- Trigger messages

## Testing

After adding your widget ID:
1. Deploy to Render
2. Visit your site
3. You should see the Tawk.to chat bubble in bottom-right corner
4. Test by sending a message
5. Reply from Tawk.to dashboard or mobile app

## Support

If you need help getting your Tawk.to widget ID:
- Email: support@dailyfundzboost.trade
- Visit: https://help.tawk.to/
