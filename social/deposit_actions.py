"""
Staff-only deposit approval/rejection views linked from email.
"""
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import render, get_object_or_404
from .models import Deposit
from .emails import send_deposit_approved_email, send_deposit_rejected_email


@login_required
def deposit_action_view(request, action, token):
    """
    Handle deposit approve/reject from email links.
    action: 'approve' or 'reject'
    token: signed token containing deposit ID. Staff must confirm via POST.
    """
    if not (request.user.is_staff or request.user.is_superuser):
        return HttpResponseForbidden('Staff access required.')

    if action not in ('approve', 'reject'):
        return HttpResponse('Invalid deposit action.', status=400)

    # Verify token and get deposit ID
    deposit_id = Deposit.verify_action_token(token, max_age=86400)  # 24 hour expiry
    
    if not deposit_id:
        return render(request, 'admin/deposit_action_result.html', {
            'success': False,
            'error': 'Invalid or expired link. This link may have been used already or expired after 24 hours.',
            'title': 'Link Expired'
        })
    
    deposit = get_object_or_404(Deposit, id=deposit_id)
    if deposit.status != 'pending':
        return render(request, 'admin/deposit_action_result.html', {
            'success': False,
            'error': f'This deposit has already been {deposit.status}.',
            'deposit': deposit,
            'title': 'Already Processed'
        })

    symbol = '₦' if deposit.currency == 'NGN' else '$'

    if request.method == 'GET':
        return render(request, 'admin/deposit_action_confirm.html', {
            'action': action,
            'deposit': deposit,
            'symbol': symbol,
        })

    if request.method != 'POST':
        return HttpResponse(status=405)

    note = request.POST.get(
        'admin_note',
        f'{"Approved" if action == "approve" else "Rejected"} via email link',
    )
    if action == 'approve':
        success = deposit.approve(request.user, note)
        if success:
            send_deposit_approved_email(deposit)
            return render(request, 'admin/deposit_action_result.html', {
                'success': True,
                'action': 'approved',
                'deposit': deposit,
                'title': '✅ Deposit Approved!',
                'message': f'Successfully approved {symbol}{deposit.amount:,.0f} for {deposit.user.username}. User has been notified via email.',
                'symbol': symbol
            })

    elif deposit.reject(request.user, note):
        send_deposit_rejected_email(deposit)
        return render(request, 'admin/deposit_action_result.html', {
            'success': True,
            'action': 'rejected',
            'deposit': deposit,
            'title': 'Deposit Rejected',
            'message': f'Rejected {symbol}{deposit.amount:,.0f} from {deposit.user.username}. User has been notified via email.',
            'symbol': symbol
        })

    return render(request, 'admin/deposit_action_result.html', {
        'success': False,
        'error': 'This deposit has already been processed.',
        'deposit': deposit,
        'title': 'Action Failed'
    })
