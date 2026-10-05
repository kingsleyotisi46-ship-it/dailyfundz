"""
GrizzlySMS API Integration for Virtual Numbers
API Documentation: https://grizzlysms.com/api
"""
import requests
from django.conf import settings


class GrizzlySMSProvider:
    """GrizzlySMS API client for virtual phone numbers"""
    
    BASE_URL = "https://api.grizzlysms.com/stubs/handler_api.php"
    
    # Service codes for popular platforms
    SERVICES = {
        'whatsapp': 'wa',
        'telegram': 'tg',
        'google': 'go',
        'facebook': 'fb',
        'instagram': 'ig',
        'tiktok': 'lf',
        'twitter': 'tw',
        'amazon': 'am',
        'paypal': 'pp',
        'apple': 'ew',
        'claude': 'ot',  # AnyOther
        'other': 'ot',
    }
    
    # Popular countries with codes
    COUNTRIES = {
        'usa': '187',
        'uk': '16',
        'canada': '36',
        'india': '22',
        'nigeria': '19',
        'south_africa': '31',
        'brazil': '73',
        'mexico': '54',
        'germany': '43',
        'france': '78',
        'italy': '86',
        'spain': '56',
        'netherlands': '48',
        'australia': '175',
        'indonesia': '6',
        'philippines': '4',
        'thailand': '52',
        'vietnam': '10',
        'pakistan': '14',
        'colombia': '33',
        'argentina': '39',
        'russia': '0',
        'ukraine': '1',
        'poland': '15',
        'turkey': '62',
        'egypt': '21',
        'kenya': '8',
        'ghana': '38',
    }
    
    def __init__(self):
        self.api_key = getattr(settings, 'GRIZZLY_API_KEY', None)
    
    def is_configured(self):
        return bool(self.api_key)
    
    def _make_request(self, action, **params):
        """Make API request to GrizzlySMS"""
        if not self.is_configured():
            return {'error': 'GrizzlySMS API key not configured'}
        
        params['api_key'] = self.api_key
        params['action'] = action
        
        try:
            response = requests.get(self.BASE_URL, params=params, timeout=30)
            return self._parse_response(response.text, action)
        except requests.RequestException as e:
            return {'error': f'API request failed: {str(e)}'}
    
    def _parse_response(self, text, action):
        """Parse GrizzlySMS response"""
        text = text.strip()
        
        # Handle different response formats
        if text.startswith('ACCESS_'):
            parts = text.split(':')
            if action == 'getNumber':
                return {
                    'success': True,
                    'activation_id': parts[1] if len(parts) > 1 else None,
                    'phone': parts[2] if len(parts) > 2 else None,
                }
            return {'success': True, 'data': parts}
        
        elif text.startswith('STATUS_'):
            status = text.replace('STATUS_', '')
            if ':' in status:
                parts = status.split(':')
                return {
                    'success': True,
                    'status': parts[0],
                    'code': parts[1] if len(parts) > 1 else None,
                }
            return {'success': True, 'status': status}
        
        elif text.startswith('BALANCE:'):
            balance = text.replace('BALANCE:', '')
            return {'success': True, 'balance': float(balance)}
        
        elif text in ['NO_NUMBERS', 'NO_BALANCE', 'BAD_KEY', 'BAD_ACTION', 'BAD_SERVICE', 'BAD_STATUS']:
            return {'success': False, 'error': text}
        
        else:
            return {'success': False, 'error': text, 'raw': text}
    
    def get_balance(self):
        """Get account balance"""
        return self._make_request('getBalance')
    
    def get_number(self, service='whatsapp', country='usa'):
        """
        Get a virtual number for SMS verification
        
        Args:
            service: Platform name (whatsapp, telegram, google, etc.)
            country: Country code or name
        
        Returns:
            dict with activation_id and phone number
        """
        service_code = self.SERVICES.get(service.lower(), 'ot')
        country_code = self.COUNTRIES.get(country.lower(), country)
        
        return self._make_request(
            'getNumber',
            service=service_code,
            country=country_code
        )
    
    def get_status(self, activation_id):
        """
        Check activation status and get SMS code
        
        Args:
            activation_id: The ID returned from get_number
        
        Returns:
            dict with status and code (if received)
        """
        return self._make_request('getStatus', id=activation_id)
    
    def set_status(self, activation_id, status):
        """
        Set activation status
        
        Args:
            activation_id: The activation ID
            status: 
                1 = Ready (inform that number is entered)
                3 = Request another SMS
                6 = Complete activation
                8 = Cancel activation
        """
        return self._make_request('setStatus', id=activation_id, status=status)
    
    def cancel_activation(self, activation_id):
        """Cancel an activation and get refund"""
        return self.set_status(activation_id, 8)
    
    def confirm_sms_received(self, activation_id):
        """Confirm that SMS was received, complete activation"""
        return self.set_status(activation_id, 6)
    
    def request_another_sms(self, activation_id):
        """Request another SMS code"""
        return self.set_status(activation_id, 3)
    
    def get_prices(self, service='whatsapp', country=None):
        """Get prices for a service"""
        service_code = self.SERVICES.get(service.lower(), 'ot')
        params = {'service': service_code}
        if country:
            params['country'] = self.COUNTRIES.get(country.lower(), country)
        return self._make_request('getPrices', **params)
    
    def get_countries(self):
        """Get list of available countries"""
        return self._make_request('getCountries')
    
    @classmethod
    def get_service_list(cls):
        """Get list of supported services for display"""
        return [
            {'code': 'whatsapp', 'name': 'WhatsApp', 'icon': '📱'},
            {'code': 'telegram', 'name': 'Telegram', 'icon': '✈️'},
            {'code': 'google', 'name': 'Google/Gmail', 'icon': '📧'},
            {'code': 'facebook', 'name': 'Facebook', 'icon': '👤'},
            {'code': 'instagram', 'name': 'Instagram', 'icon': '📸'},
            {'code': 'tiktok', 'name': 'TikTok', 'icon': '🎵'},
            {'code': 'twitter', 'name': 'Twitter/X', 'icon': '🐦'},
            {'code': 'amazon', 'name': 'Amazon', 'icon': '📦'},
            {'code': 'paypal', 'name': 'PayPal', 'icon': '💳'},
            {'code': 'apple', 'name': 'Apple', 'icon': '🍎'},
            {'code': 'other', 'name': 'Other Services', 'icon': '🔢'},
        ]
    
    @classmethod
    def get_country_list(cls):
        """Get list of popular countries for display"""
        return [
            {'code': 'usa', 'name': 'USA', 'flag': '🇺🇸'},
            {'code': 'uk', 'name': 'United Kingdom', 'flag': '🇬🇧'},
            {'code': 'canada', 'name': 'Canada', 'flag': '🇨🇦'},
            {'code': 'india', 'name': 'India', 'flag': '🇮🇳'},
            {'code': 'nigeria', 'name': 'Nigeria', 'flag': '🇳🇬'},
            {'code': 'south_africa', 'name': 'South Africa', 'flag': '🇿🇦'},
            {'code': 'germany', 'name': 'Germany', 'flag': '🇩🇪'},
            {'code': 'france', 'name': 'France', 'flag': '🇫🇷'},
            {'code': 'netherlands', 'name': 'Netherlands', 'flag': '🇳🇱'},
            {'code': 'australia', 'name': 'Australia', 'flag': '🇦🇺'},
            {'code': 'brazil', 'name': 'Brazil', 'flag': '🇧🇷'},
            {'code': 'mexico', 'name': 'Mexico', 'flag': '🇲🇽'},
            {'code': 'indonesia', 'name': 'Indonesia', 'flag': '🇮🇩'},
            {'code': 'philippines', 'name': 'Philippines', 'flag': '🇵🇭'},
            {'code': 'thailand', 'name': 'Thailand', 'flag': '🇹🇭'},
            {'code': 'vietnam', 'name': 'Vietnam', 'flag': '🇻🇳'},
            {'code': 'pakistan', 'name': 'Pakistan', 'flag': '🇵🇰'},
            {'code': 'colombia', 'name': 'Colombia', 'flag': '🇨🇴'},
            {'code': 'argentina', 'name': 'Argentina', 'flag': '🇦🇷'},
            {'code': 'russia', 'name': 'Russia', 'flag': '🇷🇺'},
            {'code': 'ukraine', 'name': 'Ukraine', 'flag': '🇺🇦'},
            {'code': 'poland', 'name': 'Poland', 'flag': '🇵🇱'},
            {'code': 'turkey', 'name': 'Turkey', 'flag': '🇹🇷'},
            {'code': 'egypt', 'name': 'Egypt', 'flag': '🇪🇬'},
            {'code': 'kenya', 'name': 'Kenya', 'flag': '🇰🇪'},
            {'code': 'ghana', 'name': 'Ghana', 'flag': '🇬🇭'},
        ]


# Global instance
grizzly_provider = GrizzlySMSProvider()
