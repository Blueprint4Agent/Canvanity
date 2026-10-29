export interface paths {
    "/api/v1/admin/demo/status": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Demo Status */
        get: operations["demo_status_api_v1_admin_demo_status_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/admin/demo/users": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Demo Users */
        get: operations["demo_users_api_v1_admin_demo_users_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/admin/status": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Status */
        get: operations["status_api_v1_admin_status_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/api-keys": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Api Keys */
        get: operations["list_api_keys_api_v1_api_keys_get"];
        put?: never;
        /** Create Api Key */
        post: operations["create_api_key_api_v1_api_keys_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/api-keys/{api_key_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        post?: never;
        /** Delete Api Key */
        delete: operations["delete_api_key_api_v1_api_keys__api_key_id__delete"];
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/api-keys/{api_key_id}/status": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        /** Update Api Key Status */
        patch: operations["update_api_key_status_api_v1_api_keys__api_key_id__status_patch"];
        trace?: never;
    };
    "/api/v1/auth/admin/user-role-stats": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Admin User Role Stats */
        get: operations["admin_user_role_stats_api_v1_auth_admin_user_role_stats_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/auth/admin/users": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Admin Users */
        get: operations["admin_users_api_v1_auth_admin_users_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/auth/forgot-password": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Forgot Password */
        post: operations["forgot_password_api_v1_auth_forgot_password_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/auth/login": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Login */
        post: operations["login_api_v1_auth_login_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/auth/logout": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /**
         * Logout
         * @description Invalidates all refresh sessions for the authenticated user and expires both refresh cookies. Already-issued access tokens remain valid until their expiry.
         */
        post: operations["logout_api_v1_auth_logout_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/auth/me": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Me */
        get: operations["me_api_v1_auth_me_get"];
        put?: never;
        post?: never;
        /**
         * Delete Me
         * @description Permanently deletes the current account, credentials, OAuth identities and API keys. Requires bearer authentication, matching email confirmation and a single-use emailed code. Clears refresh cookies; all sessions stop authenticating.
         */
        delete: operations["delete_me_api_v1_auth_me_delete"];
        options?: never;
        head?: never;
        /** Update Me */
        patch: operations["update_me_api_v1_auth_me_patch"];
        trace?: never;
    };
    "/api/v1/auth/me/deletion-code": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Request Deletion Code */
        post: operations["request_deletion_code_api_v1_auth_me_deletion_code_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/auth/me/deletion-code/verify": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Verify Deletion Code */
        post: operations["verify_deletion_code_api_v1_auth_me_deletion_code_verify_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/auth/me/password": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Change Password */
        post: operations["change_password_api_v1_auth_me_password_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/auth/me/password/code": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Request Password Change Code */
        post: operations["request_password_change_code_api_v1_auth_me_password_code_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/auth/me/password/code/verify": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Verify Password Change Code */
        post: operations["verify_password_change_code_api_v1_auth_me_password_code_verify_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/auth/me/photo": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Read Profile Photo */
        get: operations["read_profile_photo_api_v1_auth_me_photo_get"];
        /** Upload Profile Photo */
        put: operations["upload_profile_photo_api_v1_auth_me_photo_put"];
        post?: never;
        /** Delete Profile Photo */
        delete: operations["delete_profile_photo_api_v1_auth_me_photo_delete"];
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/auth/oauth/providers": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Oauth Providers */
        get: operations["oauth_providers_api_v1_auth_oauth_providers_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/auth/oauth/{provider}/callback": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Oauth Callback */
        get: operations["oauth_callback_api_v1_auth_oauth__provider__callback_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/auth/oauth/{provider}/start": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Oauth Start */
        get: operations["oauth_start_api_v1_auth_oauth__provider__start_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/auth/refresh": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /**
         * Refresh Token
         * @description Refreshes the access token and extends the existing refresh session TTL. The refresh token value is retained. Non-empty JSON fields take precedence over cookies; user_id can be resolved from the session. Browser clients may send an empty JSON object.
         */
        post: operations["refresh_token_api_v1_auth_refresh_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/auth/resend-verification": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Resend Verification Email */
        post: operations["resend_verification_email_api_v1_auth_resend_verification_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/auth/reset-password": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Reset Password */
        post: operations["reset_password_api_v1_auth_reset_password_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/auth/signup": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Signup */
        post: operations["signup_api_v1_auth_signup_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/auth/token": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Oauth Token Login */
        post: operations["oauth_token_login_api_v1_auth_token_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/auth/verify-email": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Verify Email */
        post: operations["verify_email_api_v1_auth_verify_email_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/billing/card-setups": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Create Card Setup */
        post: operations["create_card_setup_api_v1_billing_card_setups_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/billing/card-setups/{intent_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Card Setup Status */
        get: operations["card_setup_status_api_v1_billing_card_setups__intent_id__get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/billing/checkout-sessions": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Create Checkout */
        post: operations["create_checkout_api_v1_billing_checkout_sessions_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/billing/checkout-sessions/{session_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Checkout Status */
        get: operations["checkout_status_api_v1_billing_checkout_sessions__session_id__get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/billing/config": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Billing Config */
        get: operations["billing_config_api_v1_billing_config_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/billing/invoices": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Billing Invoices */
        get: operations["billing_invoices_api_v1_billing_invoices_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/billing/invoices/{invoice_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Invoice Detail */
        get: operations["invoice_detail_api_v1_billing_invoices__invoice_id__get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/billing/payment-methods": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Payment Methods */
        get: operations["list_payment_methods_api_v1_billing_payment_methods_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/billing/payment-methods/{method_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Manage Billing Method */
        post: operations["manage_billing_method_api_v1_billing_payment_methods__method_id__post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/billing/plans": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Plans */
        get: operations["plans_api_v1_billing_plans_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/billing/portal-sessions": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Billing Portal */
        post: operations["billing_portal_api_v1_billing_portal_sessions_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/billing/profile": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Billing Profile */
        get: operations["billing_profile_api_v1_billing_profile_get"];
        /** Update Billing Profile */
        put: operations["update_billing_profile_api_v1_billing_profile_put"];
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/billing/setup-sessions": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Create Setup */
        post: operations["create_setup_api_v1_billing_setup_sessions_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/billing/setup-sessions/{session_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Setup Status */
        get: operations["setup_status_api_v1_billing_setup_sessions__session_id__get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/billing/subscription": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Subscription */
        get: operations["subscription_api_v1_billing_subscription_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/billing/subscription/change": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Change Subscription */
        post: operations["change_subscription_api_v1_billing_subscription_change_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/billing/webhook": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Billing Webhook */
        post: operations["billing_webhook_api_v1_billing_webhook_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/boards": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Boards */
        get: operations["list_boards_api_v1_boards_get"];
        put?: never;
        /** Create Board */
        post: operations["create_board_api_v1_boards_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/boards/by-slug/{slug}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Home By Slug */
        get: operations["home_by_slug_api_v1_boards_by_slug__slug__get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/boards/{board_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Board Home */
        get: operations["board_home_api_v1_boards__board_id__get"];
        put?: never;
        post?: never;
        /** Delete Empty Board */
        delete: operations["delete_empty_board_api_v1_boards__board_id__delete"];
        options?: never;
        head?: never;
        /** Update Board */
        patch: operations["update_board_api_v1_boards__board_id__patch"];
        trace?: never;
    };
    "/api/v1/boards/{board_id}/canvases": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Create Canvas */
        post: operations["create_canvas_api_v1_boards__board_id__canvases_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/boards/{board_id}/grades": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Grades */
        get: operations["grades_api_v1_boards__board_id__grades_get"];
        put?: never;
        /** Create Grade */
        post: operations["create_grade_api_v1_boards__board_id__grades_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/boards/{board_id}/grades/order": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        /** Reorder Grades */
        patch: operations["reorder_grades_api_v1_boards__board_id__grades_order_patch"];
        trace?: never;
    };
    "/api/v1/boards/{board_id}/grades/{grade_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        post?: never;
        /** Delete Grade */
        delete: operations["delete_grade_api_v1_boards__board_id__grades__grade_id__delete"];
        options?: never;
        head?: never;
        /** Change Grade */
        patch: operations["change_grade_api_v1_boards__board_id__grades__grade_id__patch"];
        trace?: never;
    };
    "/api/v1/boards/{board_id}/home": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Board Home */
        get: operations["board_home_api_v1_boards__board_id__home_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/boards/{board_id}/join": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Join Board */
        post: operations["join_board_api_v1_boards__board_id__join_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/boards/{board_id}/member-audit": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Member Audit */
        get: operations["member_audit_api_v1_boards__board_id__member_audit_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/boards/{board_id}/members": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Members */
        get: operations["members_api_v1_boards__board_id__members_get"];
        put?: never;
        /** Invite Member */
        post: operations["invite_member_api_v1_boards__board_id__members_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/boards/{board_id}/members/{user_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        /** Update Member */
        patch: operations["update_member_api_v1_boards__board_id__members__user_id__patch"];
        trace?: never;
    };
    "/api/v1/boards/{board_id}/membership": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        post?: never;
        /** Leave Board */
        delete: operations["leave_board_api_v1_boards__board_id__membership_delete"];
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/boards/{board_id}/ownership-transfer": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Transfer Board Ownership */
        post: operations["transfer_board_ownership_api_v1_boards__board_id__ownership_transfer_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/boards/{board_id}/policies": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Board Policies */
        get: operations["board_policies_api_v1_boards__board_id__policies_get"];
        /** Set Board Policies */
        put: operations["set_board_policies_api_v1_boards__board_id__policies_put"];
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/boards/{board_id}/shelves": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Shelves */
        get: operations["list_shelves_api_v1_boards__board_id__shelves_get"];
        put?: never;
        /** Create Shelf */
        post: operations["create_shelf_api_v1_boards__board_id__shelves_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/boards/{board_id}/shelves/order": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        /** Reorder Shelves */
        patch: operations["reorder_shelves_api_v1_boards__board_id__shelves_order_patch"];
        trace?: never;
    };
    "/api/v1/canvases/{canvas_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Canvas */
        get: operations["get_canvas_api_v1_canvases__canvas_id__get"];
        put?: never;
        post?: never;
        /** Trash Canvas */
        delete: operations["trash_canvas_api_v1_canvases__canvas_id__delete"];
        options?: never;
        head?: never;
        /** Change Canvas */
        patch: operations["change_canvas_api_v1_canvases__canvas_id__patch"];
        trace?: never;
    };
    "/api/v1/canvases/{canvas_id}/assets": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Upload Asset */
        post: operations["upload_asset_api_v1_canvases__canvas_id__assets_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/canvases/{canvas_id}/assets/{asset_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Read Asset */
        get: operations["read_asset_api_v1_canvases__canvas_id__assets__asset_id__get"];
        put?: never;
        post?: never;
        /** Delete Asset */
        delete: operations["delete_asset_api_v1_canvases__canvas_id__assets__asset_id__delete"];
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/canvases/{canvas_id}/document": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Canvas Document */
        get: operations["get_canvas_document_api_v1_canvases__canvas_id__document_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/canvases/{canvas_id}/restore": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Restore Canvas */
        post: operations["restore_canvas_api_v1_canvases__canvas_id__restore_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/events/stream": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Stream Events */
        get: operations["stream_events_api_v1_events_stream_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/inbox": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Notifications */
        get: operations["list_notifications_api_v1_inbox_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/inbox/read-all": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Read All */
        post: operations["read_all_api_v1_inbox_read_all_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/inbox/read-selected": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Read Selected */
        post: operations["read_selected_api_v1_inbox_read_selected_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/inbox/selected": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        post?: never;
        /** Delete Selected */
        delete: operations["delete_selected_api_v1_inbox_selected_delete"];
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/inbox/summary": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Summary */
        get: operations["summary_api_v1_inbox_summary_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/inbox/{notification_id}/read": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Read */
        post: operations["read_api_v1_inbox__notification_id__read_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/inquiries": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Own */
        get: operations["list_own_api_v1_inquiries_get"];
        put?: never;
        /** Create */
        post: operations["create_api_v1_inquiries_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/inquiries/admin": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List All */
        get: operations["list_all_api_v1_inquiries_admin_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/inquiries/{inquiry_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Detail */
        get: operations["detail_api_v1_inquiries__inquiry_id__get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/inquiries/{inquiry_id}/messages": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Reply */
        post: operations["reply_api_v1_inquiries__inquiry_id__messages_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/inquiries/{inquiry_id}/status": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        /** Change Status */
        patch: operations["change_status_api_v1_inquiries__inquiry_id__status_patch"];
        trace?: never;
    };
    "/api/v1/interests": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Catalog */
        get: operations["catalog_api_v1_interests_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/interests/admin": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Admin */
        get: operations["list_admin_api_v1_interests_admin_get"];
        put?: never;
        /** Create */
        post: operations["create_api_v1_interests_admin_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/interests/admin/{interest_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        /** Update */
        patch: operations["update_api_v1_interests_admin__interest_id__patch"];
        trace?: never;
    };
    "/api/v1/shelves/{shelf_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Shelf */
        get: operations["get_shelf_api_v1_shelves__shelf_id__get"];
        put?: never;
        post?: never;
        /** Delete Shelf */
        delete: operations["delete_shelf_api_v1_shelves__shelf_id__delete"];
        options?: never;
        head?: never;
        /** Change Shelf */
        patch: operations["change_shelf_api_v1_shelves__shelf_id__patch"];
        trace?: never;
    };
    "/api/v1/shelves/{shelf_id}/policies": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Shelf Policies */
        get: operations["shelf_policies_api_v1_shelves__shelf_id__policies_get"];
        /** Set Shelf Policies */
        put: operations["set_shelf_policies_api_v1_shelves__shelf_id__policies_put"];
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/config": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Config */
        get: operations["config_config_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/health/live": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Health Live */
        get: operations["health_live_health_live_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/health/ready": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Health Ready */
        get: operations["health_ready_health_ready_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/ping": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Ping */
        get: operations["ping_ping_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
}
export type webhooks = Record<string, never>;
export interface components {
    schemas: {
        /** APIKeyCreateForm */
        APIKeyCreateForm: {
            /** Expires At */
            expires_at?: string | null;
            /** Name */
            name: string;
        };
        /** APIKeyCreateResponse */
        APIKeyCreateResponse: {
            /** Api Key */
            api_key: string;
            key: components["schemas"]["APIKeyResponse"];
        };
        /** APIKeyErrorDetail */
        APIKeyErrorDetail: {
            /** Details */
            details?: {
                [key: string]: unknown;
            } | null;
            /**
             * Error
             * @example API_KEY_NOT_FOUND
             * @enum {string}
             */
            error:
                | "API_KEY_INVALID"
                | "API_KEY_USER_MISMATCH"
                | "API_KEY_CREATE_FAILED"
                | "API_KEY_NAME_ALREADY_EXISTS"
                | "API_KEY_NOT_FOUND"
                | "API_KEY_UPDATE_FAILED";
            /** Message */
            message: string;
        };
        /** APIKeyErrorResponse */
        APIKeyErrorResponse: {
            detail: components["schemas"]["APIKeyErrorDetail"];
        };
        /** APIKeyEvent */
        APIKeyEvent: {
            /** Id */
            id: string;
            payload: components["schemas"]["APIKeyEventPayload"];
            /**
             * Ts
             * Format: date-time
             */
            ts: string;
            /**
             * @description discriminator enum property added by openapi-typescript
             * @enum {string}
             */
            type: "api_key.created" | "api_key.deleted" | "api_key.status_updated";
            /**
             * Version
             * @default v1
             */
            version: string;
        };
        /** APIKeyEventPayload */
        APIKeyEventPayload: {
            api_key: components["schemas"]["APIKeyResponse"];
        };
        /** APIKeyResponse */
        APIKeyResponse: {
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
            /** Expires At */
            expires_at?: string | null;
            /** Id */
            id: number;
            /** Key Prefix */
            key_prefix: string;
            /** Last Used At */
            last_used_at?: string | null;
            /** Name */
            name: string;
            /** Request Count */
            request_count: number;
            /** Revoked At */
            revoked_at?: string | null;
        };
        /** APIKeyStatusUpdateForm */
        APIKeyStatusUpdateForm: {
            /** Enabled */
            enabled: boolean;
        };
        /** APIKeysResponse */
        APIKeysResponse: {
            /** Items */
            items: components["schemas"]["APIKeyResponse"][];
        };
        /** ActionPolicy */
        ActionPolicy: {
            /**
             * Audience
             * @enum {string}
             */
            audience: "public" | "members";
            /** Min Grade Id */
            min_grade_id?: string | null;
            /**
             * Staff Bypass
             * @default true
             */
            staff_bypass: boolean;
            /**
             * Staff Only
             * @default false
             */
            staff_only: boolean;
        };
        /** AdminConnection */
        AdminConnection: {
            /** Checked At */
            checked_at?: string | null;
            /** Host */
            host?: string | null;
            /**
             * Id
             * @enum {string}
             */
            id: "server" | "database" | "cache" | "object_storage";
            /** Latency Ms */
            latency_ms?: number | null;
            /** Port */
            port?: number | null;
            /** Probe */
            probe?: ("local_io" | "bucket_access") | null;
            /**
             * Status
             * @enum {string}
             */
            status: "ok" | "failed" | "timeout";
            /**
             * Technology
             * @enum {string}
             */
            technology:
                | "fastapi"
                | "sqlite"
                | "postgresql"
                | "mysql"
                | "mariadb"
                | "database"
                | "redis"
                | "memory"
                | "local"
                | "s3"
                | "r2"
                | "supabase";
            /** Transport */
            transport?: ("filesystem" | "https" | "http") | null;
        };
        /** AdminEnvironment */
        AdminEnvironment: {
            /**
             * Admin Access
             * @default admin_only
             * @constant
             */
            admin_access: "admin_only";
            /**
             * App Mode
             * @enum {string}
             */
            app_mode: "development" | "production";
            /** Billing Configured */
            billing_configured: boolean;
            /** Billing Enabled */
            billing_enabled: boolean;
            /**
             * Billing Mode
             * @enum {string}
             */
            billing_mode: "disabled" | "test" | "live";
            /** Developer Enabled */
            developer_enabled: boolean;
            /** Email Enabled */
            email_enabled: boolean;
            /** Login Enabled */
            login_enabled: boolean;
            /** Oauth Enabled */
            oauth_enabled: boolean;
            /** Oauth Providers */
            oauth_providers: string[];
            /** Redis In Memory */
            redis_in_memory: boolean;
        };
        /** AdminEnvironmentValues */
        AdminEnvironmentValues: {
            /**
             * App Mode
             * @enum {string}
             */
            APP_MODE: "development" | "production";
            /** Email Enabled */
            EMAIL_ENABLED: boolean;
            /** Login Enabled */
            LOGIN_ENABLED: boolean;
            /** Oauth Enabled */
            OAUTH_ENABLED: boolean;
            /** Redis In Memory */
            REDIS_IN_MEMORY: boolean;
            /** Stripe Enabled */
            STRIPE_ENABLED: boolean;
        };
        /** AdminErrorDetail */
        AdminErrorDetail: {
            /** Details */
            details?: {
                [key: string]: unknown;
            } | null;
            /**
             * Error
             * @example ADMIN_STATUS_FAILED
             * @enum {string}
             */
            error: "ADMIN_DEMO_DISABLED" | "ADMIN_DEMO_FAILED" | "ADMIN_STATUS_FAILED";
            /** Message */
            message: string;
        };
        /** AdminErrorResponse */
        AdminErrorResponse: {
            detail: components["schemas"]["AdminErrorDetail"];
        };
        /** AdminStatusResponse */
        AdminStatusResponse: {
            /**
             * Checked At
             * Format: date-time
             */
            checked_at: string;
            /** Connections */
            connections: components["schemas"]["AdminConnection"][];
            environment: components["schemas"]["AdminEnvironment"];
            environment_values: components["schemas"]["AdminEnvironmentValues"];
            /** Integration Checks */
            integration_checks: {
                [key: string]: components["schemas"]["IntegrationCheck"];
            };
            /** Startup Checks */
            startup_checks: {
                [key: string]: components["schemas"]["StartupCheck"];
            };
            /**
             * Status
             * @enum {string}
             */
            status: "ok" | "degraded";
        };
        /** AdminUserListResponse */
        AdminUserListResponse: {
            /** Items */
            items: components["schemas"]["AdminUserResponse"][];
            /** Page */
            page: number;
            /** Page Size */
            page_size: number;
            summary: components["schemas"]["UserRoleStatsResponse"];
            /** Total */
            total: number;
        };
        /** AdminUserResponse */
        AdminUserResponse: {
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
            /** Email */
            email: string;
            /** Id */
            id: number;
            /** Is Active */
            is_active: boolean;
            /** Is Verified */
            is_verified: boolean;
            /** Last Login At */
            last_login_at: string | null;
            /** Login Providers */
            login_providers: string[];
            /** Name */
            name: string;
            role: components["schemas"]["UserRole"];
        };
        /** AppConfigResponse */
        AppConfigResponse: {
            /** Api Base Path */
            api_base_path: string;
            /**
             * App Layout
             * @default sidebar
             * @enum {string}
             */
            app_layout: "sidebar" | "topnav" | "focused";
            /**
             * App Mode
             * @enum {string}
             */
            app_mode: "development" | "production";
            /** Billing Enabled */
            billing_enabled: boolean;
            /** Bootstrap Access Token */
            bootstrap_access_token?: string | null;
            bootstrap_user?: components["schemas"]["UserResponse"] | null;
            /**
             * Demo Enabled
             * @default false
             */
            demo_enabled: boolean;
            /** Email Enabled */
            email_enabled: boolean;
            /** Frontend Base Path */
            frontend_base_path: string;
            /** Login Enabled */
            login_enabled: boolean;
            /** Oauth Enabled */
            oauth_enabled: boolean;
            /** Oauth Providers */
            oauth_providers: string[];
        };
        /** AssetErrorDetail */
        AssetErrorDetail: {
            /** Details */
            details?: {
                [key: string]: unknown;
            } | null;
            /**
             * Error
             * @example ASSET_NOT_FOUND
             * @enum {string}
             */
            error:
                | "ASSET_LIMIT_REACHED"
                | "ASSET_NOT_FOUND"
                | "ASSET_INVALID_IMAGE"
                | "ASSET_TOO_LARGE"
                | "ASSET_CONFLICT"
                | "ASSET_REFERENCED"
                | "ASSET_INVALID_REFERENCE"
                | "ASSET_UNAVAILABLE";
            /** Message */
            message: string;
        };
        /** AssetErrorResponse */
        AssetErrorResponse: {
            detail: components["schemas"]["AssetErrorDetail"];
        };
        /** AssetResponse */
        AssetResponse: {
            /** Byte Size */
            byte_size: number;
            /**
             * Canvas Id
             * Format: uuid
             */
            canvas_id: string;
            /**
             * Content Type
             * @constant
             */
            content_type: "image/webp";
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
            /** Expires At */
            expires_at: string | null;
            /** Frame Count */
            frame_count: number;
            /** Height */
            height: number;
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /**
             * State
             * @constant
             */
            state: "ready";
            /** Url */
            url: string;
            /** Width */
            width: number;
        };
        /** AuthErrorDetail */
        AuthErrorDetail: {
            /** Details */
            details?: {
                [key: string]: unknown;
            } | null;
            /**
             * Error
             * @example INVALID_TOKEN
             * @enum {string}
             */
            error:
                | "PASSWORD_CHANGE_CODE_INVALID"
                | "PASSWORD_CHANGE_CODE_THROTTLED"
                | "PASSWORD_CHANGE_CODE_SEND_FAILED"
                | "PASSWORD_CHANGE_FAILED"
                | "ACCOUNT_BILLING_REVIEW_REQUIRED"
                | "ACCOUNT_DELETE_CODE_INVALID"
                | "ACCOUNT_DELETE_CODE_THROTTLED"
                | "ACCOUNT_DELETE_CODE_SEND_FAILED"
                | "ACCOUNT_DELETE_FAILED"
                | "ACCOUNT_DELETE_CONFIRMATION_REQUIRED"
                | "BOARD_OWNERSHIP_REQUIRED"
                | "LAST_ADMIN_REQUIRED"
                | "ADMIN_USERS_FAILED"
                | "SIGNUP_FAILED"
                | "EMAIL_ALREADY_EXISTS"
                | "INVALID_CREDENTIALS"
                | "ACCOUNT_LOCKED"
                | "EMAIL_NOT_VERIFIED"
                | "LOGIN_DISABLED"
                | "EMAIL_DISABLED"
                | "INVALID_TOKEN"
                | "INSUFFICIENT_ROLE"
                | "USER_NOT_FOUND"
                | "PROFILE_PHOTO_INVALID"
                | "PROFILE_PHOTO_TOO_LARGE"
                | "PROFILE_PHOTO_UNAVAILABLE"
                | "PROFILE_PHOTO_NOT_FOUND"
                | "PROFILE_PHOTO_CONFLICT"
                | "INTEREST_ALREADY_EXISTS"
                | "INTEREST_NOT_FOUND"
                | "INTEREST_NOT_AVAILABLE"
                | "HANDLE_ALREADY_EXISTS"
                | "PROFILE_UPDATE_FAILED"
                | "OAUTH_PROVIDER_NOT_ENABLED"
                | "OAUTH_PROVIDER_CONFIG_INVALID"
                | "OAUTH_IDENTITY_CONFLICT"
                | "OAUTH_SIGNUP_FAILED"
                | "OAUTH_PROVIDER_REQUEST_FAILED";
            /** Message */
            message: string;
        };
        /** AuthErrorResponse */
        AuthErrorResponse: {
            detail: components["schemas"]["AuthErrorDetail"];
        };
        /** BillingAddress */
        BillingAddress: {
            /**
             * City
             * @default
             */
            city: string;
            /**
             * Country
             * @default
             */
            country: string;
            /**
             * Line1
             * @default
             */
            line1: string;
            /**
             * Line2
             * @default
             */
            line2: string;
            /**
             * Postal Code
             * @default
             */
            postal_code: string;
            /**
             * State
             * @default
             */
            state: string;
        };
        /** BillingCardSetupResponse */
        BillingCardSetupResponse: {
            /** Client Secret */
            client_secret: string;
            /** Id */
            id: string;
        };
        /** BillingCardSetupStatus */
        BillingCardSetupStatus: {
            /** Registered */
            registered: boolean;
        };
        /** BillingChangeForm */
        BillingChangeForm: {
            /** Expected Version */
            expected_version: string;
            /**
             * Plan
             * @enum {string}
             */
            plan: "free" | "monthly" | "annual" | "pro_monthly" | "pro_annual" | "keep";
            /**
             * Request Id
             * Format: uuid
             * @description Reuse this UUID when retrying the same setup request.
             */
            request_id: string;
        };
        /** BillingCheckoutForm */
        BillingCheckoutForm: {
            /**
             * Currency
             * @enum {string}
             */
            currency: "krw" | "usd";
            /**
             * Plan
             * @enum {string}
             */
            plan: "monthly" | "annual" | "pro_monthly" | "pro_annual";
            /**
             * Request Id
             * Format: uuid
             * @description Reuse this UUID when retrying the same setup request.
             */
            request_id: string;
        };
        /** BillingCheckoutStatusResponse */
        BillingCheckoutStatusResponse: {
            /** Id */
            id: string;
            /** Paid */
            paid: boolean;
            /**
             * Status
             * @enum {string}
             */
            status: "open" | "complete" | "expired";
        };
        /** BillingConfigResponse */
        BillingConfigResponse: {
            /** Enabled */
            enabled: boolean;
            /** Livemode */
            livemode: boolean;
            /** Publishable Key */
            publishable_key?: string | null;
        };
        /** BillingErrorDetail */
        BillingErrorDetail: {
            /** Details */
            details?: {
                [key: string]: unknown;
            } | null;
            /**
             * Error
             * @example BILLING_DISABLED
             * @enum {string}
             */
            error:
                | "BILLING_WEBHOOK_INVALID"
                | "BILLING_WEBHOOK_UNAVAILABLE"
                | "BILLING_DISABLED"
                | "BILLING_UNAVAILABLE"
                | "BILLING_PLAN_UNAVAILABLE"
                | "BILLING_CHECKOUT_CONFLICT"
                | "BILLING_CHANGE_CONFLICT"
                | "BILLING_METHOD_REQUIRED"
                | "BILLING_NOT_FOUND"
                | "BILLING_RECONCILIATION_REQUIRED";
            /** Message */
            message: string;
        };
        /** BillingErrorResponse */
        BillingErrorResponse: {
            detail: components["schemas"]["BillingErrorDetail"];
        };
        /** BillingInvoiceDetail */
        BillingInvoiceDetail: {
            /** Amount */
            amount: number;
            /** Amount Due */
            amount_due: number;
            /** Amount Paid */
            amount_paid: number;
            /** Created */
            created: number;
            /** Currency */
            currency: string;
            /** Id */
            id: string;
            /** Lines */
            lines: components["schemas"]["BillingInvoiceLine"][];
            /**
             * Lines Has More
             * @default false
             */
            lines_has_more: boolean;
            /** Number */
            number?: string | null;
            /** Pdf Url */
            pdf_url?: string | null;
            /** Status */
            status: string;
            /** Subtotal */
            subtotal: number;
            /** Total */
            total: number;
            /** Url */
            url?: string | null;
        };
        /** BillingInvoiceLine */
        BillingInvoiceLine: {
            /** Amount */
            amount: number;
            /** Description */
            description: string;
            /** Quantity */
            quantity?: number | null;
        };
        /** BillingInvoiceResponse */
        BillingInvoiceResponse: {
            /** Amount */
            amount: number;
            /** Created */
            created: number;
            /** Currency */
            currency: string;
            /** Id */
            id: string;
            /** Number */
            number?: string | null;
            /** Status */
            status: string;
            /** Url */
            url?: string | null;
        };
        /** BillingInvoicesResponse */
        BillingInvoicesResponse: {
            /** Has More */
            has_more: boolean;
            /** Items */
            items: components["schemas"]["BillingInvoiceResponse"][];
            /** Next Cursor */
            next_cursor?: string | null;
        };
        /** BillingMethodForm */
        BillingMethodForm: {
            /**
             * Action
             * @enum {string}
             */
            action: "default" | "remove";
            /**
             * Request Id
             * Format: uuid
             * @description Reuse this UUID when retrying the same setup request.
             */
            request_id: string;
        };
        /** BillingPaymentMethodResponse */
        BillingPaymentMethodResponse: {
            /** Brand */
            brand?: string | null;
            /** Exp Month */
            exp_month?: number | null;
            /** Exp Year */
            exp_year?: number | null;
            /** Id */
            id: string;
            /** Last4 */
            last4?: string | null;
            /**
             * Type
             * @enum {string}
             */
            type: "card" | "link";
        };
        /** BillingPaymentMethodsResponse */
        BillingPaymentMethodsResponse: {
            /** Has More */
            has_more: boolean;
            /** Items */
            items: components["schemas"]["BillingPaymentMethodResponse"][];
            /** Next Cursor */
            next_cursor?: string | null;
        };
        /** BillingPlansResponse */
        BillingPlansResponse: {
            /** Enabled */
            enabled: boolean;
            /** Livemode */
            livemode: boolean;
            /** Prices */
            prices: components["schemas"]["BillingPriceResponse"][];
        };
        /** BillingPortalForm */
        BillingPortalForm: {
            /**
             * Flow
             * @default overview
             * @enum {string}
             */
            flow: "overview" | "payment_method_update" | "customer_update";
            /**
             * Request Id
             * Format: uuid
             * @description Reuse this UUID when retrying the same setup request.
             */
            request_id: string;
        };
        /** BillingPriceResponse */
        BillingPriceResponse: {
            /**
             * Amount
             * @description Minor currency units; KRW has no decimal places.
             */
            amount: number;
            /**
             * Currency
             * @enum {string}
             */
            currency: "krw" | "usd";
            /**
             * Plan
             * @enum {string}
             */
            plan: "monthly" | "annual" | "pro_monthly" | "pro_annual";
        };
        /** BillingProfileForm */
        BillingProfileForm: {
            address: components["schemas"]["BillingAddress"];
            /** Email */
            email: string;
            /** Name */
            name: string;
            /**
             * Request Id
             * Format: uuid
             * @description Reuse this UUID when retrying the same setup request.
             */
            request_id: string;
        };
        /** BillingProfileResponse */
        BillingProfileResponse: {
            /** Address */
            address?: string[];
            address_fields?: components["schemas"]["BillingAddress"];
            /** Default Payment Method */
            default_payment_method?: string | null;
            /** Email */
            email?: string | null;
            /** Name */
            name?: string | null;
            /**
             * Portal Enabled
             * @default false
             */
            portal_enabled: boolean;
        };
        /** BillingSetupForm */
        BillingSetupForm: {
            /**
             * Request Id
             * Format: uuid
             * @description Reuse this UUID when retrying the same setup request.
             */
            request_id: string;
        };
        /** BillingSetupResponse */
        BillingSetupResponse: {
            /** Id */
            id: string;
            /** Url */
            url: string;
        };
        /** BillingSetupStatusResponse */
        BillingSetupStatusResponse: {
            /** Id */
            id: string;
            /** Registered */
            registered: boolean;
            /**
             * Status
             * @enum {string}
             */
            status: "open" | "complete" | "expired";
        };
        /** BillingSubscriptionResponse */
        BillingSubscriptionResponse: {
            /**
             * Can Manage
             * @default false
             */
            can_manage: boolean;
            /**
             * Cancel At Period End
             * @default false
             */
            cancel_at_period_end: boolean;
            /** Change Version */
            change_version?: string | null;
            /** Currency */
            currency?: string | null;
            /** Current Period End */
            current_period_end?: number | null;
            /**
             * Has Subscription
             * @default false
             */
            has_subscription: boolean;
            /**
             * Payment Required
             * @default false
             */
            payment_required: boolean;
            /** Payment Url */
            payment_url?: string | null;
            /** Pending Effective At */
            pending_effective_at?: number | null;
            /** Pending Plan */
            pending_plan?: ("free" | "monthly" | "annual" | "pro_monthly" | "pro_annual") | null;
            /**
             * Plan
             * @enum {string}
             */
            plan: "free" | "monthly" | "annual" | "pro_monthly" | "pro_annual" | "unknown";
            /** Status */
            status: string;
        };
        /** BoardAuditPageResponse */
        BoardAuditPageResponse: {
            /** Board Revision */
            board_revision: number;
            /** Items */
            items: components["schemas"]["BoardMemberAuditResponse"][];
            /** Next Cursor */
            next_cursor?: string | null;
        };
        /** BoardAuditState */
        BoardAuditState: {
            /** Grade Id */
            grade_id?: string | null;
            /** Role */
            role?: ("owner" | "admin" | "moderator" | "member") | null;
            /** Status */
            status?: ("active" | "pending" | "suspended" | "banned") | null;
        };
        /** BoardCreateForm */
        BoardCreateForm: {
            /**
             * Description
             * @default
             */
            description: string;
            /** Interest Ids */
            interest_ids?: string[];
            /**
             * Join Policy
             * @default open
             * @enum {string}
             */
            join_policy: "open" | "invite";
            /** Name */
            name: string;
            /** Slug */
            slug: string;
            /**
             * Visibility
             * @default public
             * @enum {string}
             */
            visibility: "public" | "private";
        };
        /** BoardDeleteForm */
        BoardDeleteForm: {
            /** Confirm Slug */
            confirm_slug: string;
            /** Expected Revision */
            expected_revision: number;
        };
        /** BoardErrorDetail */
        BoardErrorDetail: {
            /** Details */
            details?: {
                [key: string]: unknown;
            } | null;
            /**
             * Error
             * @example BOARD_NOT_FOUND
             * @enum {string}
             */
            error:
                | "BOARD_NOT_FOUND"
                | "BOARD_FORBIDDEN"
                | "BOARD_SLUG_TAKEN"
                | "BOARD_LIMIT_REACHED"
                | "BOARD_INVALID_INTEREST"
                | "BOARD_INVALID_SETTINGS"
                | "BOARD_INVALID_CURSOR"
                | "BOARD_REVISION_CONFLICT"
                | "BOARD_DELETE_CONFIRMATION"
                | "BOARD_NOT_EMPTY"
                | "BOARD_OWNER_CANNOT_LEAVE"
                | "BOARD_MEMBER_NOT_FOUND"
                | "BOARD_INVITEE_NOT_FOUND"
                | "BOARD_INVITATION_CONFLICT"
                | "BOARD_INVALID_OWNERSHIP_TARGET"
                | "BOARD_INVALID_GRADE"
                | "BOARD_GRADE_NOT_FOUND"
                | "BOARD_GRADE_NAME_TAKEN"
                | "BOARD_GRADE_RANK_TAKEN"
                | "BOARD_GRADE_LIMIT_REACHED"
                | "BOARD_INVALID_GRADE_ORDER"
                | "BOARD_LAST_GRADE"
                | "BOARD_INVALID_MEMBER_CHANGE"
                | "BOARD_INVALID_AUDIT_WINDOW"
                | "BOARD_UNAVAILABLE";
            /** Message */
            message: string;
        };
        /** BoardErrorResponse */
        BoardErrorResponse: {
            detail: components["schemas"]["BoardErrorDetail"];
        };
        /** BoardGradeAuditChange */
        BoardGradeAuditChange: {
            /** After */
            after: components["schemas"]["GradeSummary"][];
            /** Before */
            before: components["schemas"]["GradeSummary"][];
            /**
             * Reassigned Board Policies
             * @default 0
             */
            reassigned_board_policies: number;
            /**
             * Reassigned Members
             * @default 0
             */
            reassigned_members: number;
            /**
             * Reassigned Shelf Policies
             * @default 0
             */
            reassigned_shelf_policies: number;
            /** Replacement Grade Id */
            replacement_grade_id?: string | null;
        };
        /** BoardGradeCreateForm */
        BoardGradeCreateForm: {
            /** Expected Revision */
            expected_revision: number;
            /** Name */
            name: string;
            /** Rank */
            rank: number;
            /** Reason */
            reason: string;
        };
        /** BoardGradeDeleteForm */
        BoardGradeDeleteForm: {
            /** Expected Revision */
            expected_revision: number;
            /** Reason */
            reason: string;
            /**
             * Replacement Grade Id
             * Format: uuid
             */
            replacement_grade_id: string;
        };
        /** BoardGradeOrderForm */
        BoardGradeOrderForm: {
            /** Expected Revision */
            expected_revision: number;
            /** Grade Ids */
            grade_ids: string[];
            /** Reason */
            reason: string;
        };
        /** BoardGradePatchForm */
        BoardGradePatchForm: {
            /** Expected Revision */
            expected_revision: number;
            /**
             * Is Default
             * @constant
             */
            is_default?: true;
            /** Name */
            name?: string;
            /** Reason */
            reason: string;
        } & (
            | {
                  /** Name */
                  name: string;
              }
            | {
                  /**
                   * Is Default
                   * @constant
                   */
                  is_default: true;
              }
        );
        /** BoardGradeResponse */
        BoardGradeResponse: {
            /** Board Revision */
            board_revision: number;
            grade: components["schemas"]["GradeSummary"];
        };
        /** BoardGradesResponse */
        BoardGradesResponse: {
            /** Board Revision */
            board_revision: number;
            /** Items */
            items: components["schemas"]["GradeSummary"][];
        };
        /** BoardHomeResponse */
        BoardHomeResponse: {
            board: components["schemas"]["BoardSummary"];
            /** Grades */
            grades: components["schemas"]["GradeSummary"][];
            /** Layout */
            layout: {
                [key: string]: unknown;
            };
            /** Layout Revision */
            layout_revision: number;
            membership: components["schemas"]["MembershipSummary"] | null;
            /** Rules */
            rules: string;
            /** Shelves */
            shelves: components["schemas"]["ShelfSummary"][];
        };
        /** BoardMemberAuditResponse */
        BoardMemberAuditResponse: {
            /** Action */
            action: string;
            /** Actor User Id */
            actor_user_id: number | null;
            after?: components["schemas"]["BoardAuditState"] | null;
            before?: components["schemas"]["BoardAuditState"] | null;
            board_change?: components["schemas"]["BoardSettingsAuditChange"] | null;
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
            grade_change?: components["schemas"]["BoardGradeAuditChange"] | null;
            /**
             * Id
             * Format: uuid
             */
            id: string;
            ownership_change?: components["schemas"]["BoardOwnershipAuditChange"] | null;
            policy_change?: components["schemas"]["PolicyAuditChange"] | null;
            /** Reason */
            reason?: string | null;
            shelf_change?: components["schemas"]["ShelfAuditChange"] | null;
            /** Target User Id */
            target_user_id: number | null;
        };
        /** BoardMemberDetail */
        BoardMemberDetail: {
            /**
             * Grade Id
             * Format: uuid
             */
            grade_id: string;
            /** Grade Name */
            grade_name: string;
            /** Grade Rank */
            grade_rank: number;
            /** Handle */
            handle: string | null;
            /**
             * Joined At
             * Format: date-time
             */
            joined_at: string;
            /** Name */
            name: string;
            /**
             * Role
             * @enum {string}
             */
            role: "owner" | "admin" | "moderator" | "member";
            /**
             * Status
             * @enum {string}
             */
            status: "active" | "pending" | "suspended" | "banned";
            /** User Id */
            user_id: number;
        };
        /** BoardMemberInviteForm */
        BoardMemberInviteForm: {
            /** Expected Revision */
            expected_revision: number;
            /** Reason */
            reason: string;
            /** User Id */
            user_id: number;
        };
        /** BoardMemberListResponse */
        BoardMemberListResponse: {
            /** Board Revision */
            board_revision: number;
            /** Items */
            items: (
                | components["schemas"]["BoardMemberDetail"]
                | components["schemas"]["BoardMemberPublic"]
            )[];
            /** Next Cursor */
            next_cursor?: string | null;
            /**
             * Scope
             * @enum {string}
             */
            scope: "management" | "moderation";
        };
        /** BoardMemberPatchForm */
        BoardMemberPatchForm: {
            /** Expected Revision */
            expected_revision: number;
            /**
             * Grade Id
             * Format: uuid
             */
            grade_id?: string;
            /** Reason */
            reason: string;
            /**
             * Role
             * @enum {string}
             */
            role?: "admin" | "moderator" | "member";
            /**
             * Status
             * @enum {string}
             */
            status?: "active" | "suspended" | "banned";
        } & (
            | {
                  /**
                   * Role
                   * @enum {string}
                   */
                  role: "admin" | "moderator" | "member";
              }
            | {
                  /**
                   * Status
                   * @enum {string}
                   */
                  status: "active" | "suspended" | "banned";
              }
            | {
                  /**
                   * Grade Id
                   * Format: uuid
                   */
                  grade_id: string;
              }
        );
        /** BoardMemberPublic */
        BoardMemberPublic: {
            /** Handle */
            handle: string | null;
            /** Name */
            name: string;
            /** User Id */
            user_id: number;
        };
        /** BoardMemberUpdateResponse */
        BoardMemberUpdateResponse: {
            /** Board Revision */
            board_revision: number;
            member: components["schemas"]["BoardMemberDetail"];
        };
        /** BoardOwnershipAuditChange */
        BoardOwnershipAuditChange: {
            after: components["schemas"]["BoardOwnershipState"];
            before: components["schemas"]["BoardOwnershipState"];
        };
        /** BoardOwnershipMemberState */
        BoardOwnershipMemberState: {
            /**
             * Grade Id
             * Format: uuid
             */
            grade_id: string;
            /**
             * Role
             * @enum {string}
             */
            role: "owner" | "admin" | "moderator" | "member";
            /**
             * Status
             * @enum {string}
             */
            status: "active" | "pending" | "suspended" | "banned";
            /** User Id */
            user_id: number;
        };
        /** BoardOwnershipState */
        BoardOwnershipState: {
            /** Members */
            members: components["schemas"]["BoardOwnershipMemberState"][];
            /** Owner Id */
            owner_id: number;
        };
        /** BoardOwnershipTransferForm */
        BoardOwnershipTransferForm: {
            /** Expected Revision */
            expected_revision: number;
            /** Reason */
            reason: string;
            /** Target User Id */
            target_user_id: number;
        };
        /** BoardOwnershipTransferResponse */
        BoardOwnershipTransferResponse: {
            /**
             * Board Id
             * Format: uuid
             */
            board_id: string;
            /** Board Revision */
            board_revision: number;
            /** Owner Id */
            owner_id: number;
            /** Previous Owner Id */
            previous_owner_id: number;
        };
        /** BoardPageResponse */
        BoardPageResponse: {
            /** Items */
            items: components["schemas"]["BoardSummary"][];
            /** Next Cursor */
            next_cursor?: string | null;
        };
        /** BoardPoliciesForm */
        BoardPoliciesForm: {
            actions: components["schemas"]["BoardPolicyActions"];
            /** Expected Revision */
            expected_revision: number;
            /** Reason */
            reason: string;
        };
        /** BoardPoliciesResponse */
        BoardPoliciesResponse: {
            actions: components["schemas"]["BoardPolicyActions"];
            /**
             * Board Id
             * Format: uuid
             */
            board_id: string;
            /** Board Revision */
            board_revision: number;
        };
        /** BoardPolicyActions */
        BoardPolicyActions: {
            create_canvas: components["schemas"]["ActionPolicy"];
            create_comment: components["schemas"]["ActionPolicy"];
            react: components["schemas"]["ActionPolicy"];
            read_canvas: components["schemas"]["ActionPolicy"];
        };
        /** BoardSettingsAuditChange */
        BoardSettingsAuditChange: {
            after: components["schemas"]["BoardSettingsState"];
            before: components["schemas"]["BoardSettingsState"];
        };
        /** BoardSettingsPatchForm */
        BoardSettingsPatchForm: {
            /** Description */
            description?: string;
            /** Expected Revision */
            expected_revision: number;
            /** Interest Ids */
            interest_ids?: string[];
            /**
             * Join Policy
             * @enum {string}
             */
            join_policy?: "open" | "invite";
            /** Name */
            name?: string;
            /** Reason */
            reason: string;
            /** Rules */
            rules?: string;
            /**
             * Status
             * @enum {string}
             */
            status?: "active" | "archived";
            /**
             * Visibility
             * @enum {string}
             */
            visibility?: "public" | "private";
        } & (
            | {
                  /** Name */
                  name: string;
              }
            | {
                  /** Description */
                  description: string;
              }
            | {
                  /** Rules */
                  rules: string;
              }
            | {
                  /** Interest Ids */
                  interest_ids: string[];
              }
            | {
                  /**
                   * Visibility
                   * @enum {string}
                   */
                  visibility: "public" | "private";
              }
            | {
                  /**
                   * Join Policy
                   * @enum {string}
                   */
                  join_policy: "open" | "invite";
              }
            | {
                  /**
                   * Status
                   * @enum {string}
                   */
                  status: "active" | "archived";
              }
        );
        /** BoardSettingsState */
        BoardSettingsState: {
            /** Description */
            description: string;
            /** Interest Ids */
            interest_ids: string[];
            /**
             * Join Policy
             * @enum {string}
             */
            join_policy: "open" | "invite";
            /** Name */
            name: string;
            /** Rules */
            rules: string;
            /**
             * Status
             * @enum {string}
             */
            status: "active" | "archived" | "suspended";
            /**
             * Visibility
             * @enum {string}
             */
            visibility: "public" | "private";
        };
        /** BoardSummary */
        BoardSummary: {
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
            /** Description */
            description: string;
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /** Interest Ids */
            interest_ids: string[];
            /**
             * Join Policy
             * @enum {string}
             */
            join_policy: "open" | "invite";
            /** Name */
            name: string;
            /** Owner Id */
            owner_id: number;
            /** Revision */
            revision: number;
            /** Slug */
            slug: string;
            /**
             * Status
             * @enum {string}
             */
            status: "active" | "archived" | "suspended";
            /**
             * Visibility
             * @enum {string}
             */
            visibility: "public" | "private";
        };
        /** BoardUpdateResponse */
        BoardUpdateResponse: {
            board: components["schemas"]["BoardSummary"];
            /** Board Revision */
            board_revision: number;
            /** Rules */
            rules: string;
        };
        /** Body_oauth_token_login_api_v1_auth_token_post */
        Body_oauth_token_login_api_v1_auth_token_post: {
            /** Client Id */
            client_id?: string | null;
            /**
             * Client Secret
             * Format: password
             */
            client_secret?: string | null;
            /** Grant Type */
            grant_type?: string | null;
            /**
             * Password
             * Format: password
             */
            password: string;
            /**
             * Scope
             * @default
             */
            scope: string;
            /** Username */
            username: string;
        };
        /** Body_refresh_token_api_v1_auth_refresh_post */
        Body_refresh_token_api_v1_auth_refresh_post: {
            /** Refresh Token */
            refresh_token?: string | null;
            /** Session Id */
            session_id?: string | null;
            /** User Id */
            user_id?: number | null;
        };
        /** Body_upload_asset_api_v1_canvases__canvas_id__assets_post */
        Body_upload_asset_api_v1_canvases__canvas_id__assets_post: {
            /** File */
            file: string;
        };
        /** CanvasCapabilities */
        CanvasCapabilities: {
            /** Edit Metadata */
            edit_metadata: boolean;
            /** Read Document */
            read_document: boolean;
            /** Restore */
            restore: boolean;
            /** Trash */
            trash: boolean;
        };
        /** CanvasContent */
        CanvasContent: {
            /** Edges */
            edges?: {
                [key: string]: unknown;
            }[];
            /** Element Order */
            element_order?: string[];
            engine?: components["schemas"]["CanvasEngine"];
            /** Nodes */
            nodes?: {
                [key: string]: unknown;
            }[];
            /**
             * Schema Version
             * @default 1
             * @constant
             */
            schema_version: 1;
            settings?: components["schemas"]["CanvasSettings"];
        };
        /** CanvasCreateForm */
        CanvasCreateForm: {
            /**
             * Shelf Id
             * Format: uuid
             */
            shelf_id: string;
            /**
             * Summary
             * @default
             */
            summary: string;
            /** Title */
            title: string;
            /**
             * Visibility
             * @default members
             * @enum {string}
             */
            visibility: "public" | "members";
        };
        /** CanvasDocumentResponse */
        CanvasDocumentResponse: {
            document: components["schemas"]["CanvasContent"];
            /** Revision */
            revision: number;
            /**
             * View
             * @default draft
             * @constant
             */
            view: "draft";
        };
        /** CanvasEngine */
        CanvasEngine: {
            /**
             * Adapter Version
             * @default 1
             * @constant
             */
            adapter_version: 1;
            /**
             * Name
             * @default excalidraw
             * @constant
             */
            name: "excalidraw";
            /**
             * Version
             * @default 0.18.1
             * @constant
             */
            version: "0.18.1";
        };
        /** CanvasErrorDetail */
        CanvasErrorDetail: {
            /** Details */
            details?: {
                [key: string]: unknown;
            } | null;
            /**
             * Error
             * @example CANVAS_NOT_FOUND
             * @enum {string}
             */
            error:
                | "CANVAS_NOT_FOUND"
                | "CANVAS_FORBIDDEN"
                | "CANVAS_INVALID_SHELF"
                | "CANVAS_REVISION_CONFLICT"
                | "CANVAS_INVALID_STATE"
                | "CANVAS_RESTORE_EXPIRED"
                | "CANVAS_UNAVAILABLE";
            /** Message */
            message: string;
        };
        /** CanvasErrorResponse */
        CanvasErrorResponse: {
            detail: components["schemas"]["CanvasErrorDetail"];
        };
        /** CanvasMetadata */
        CanvasMetadata: {
            /** Author Id */
            author_id: number | null;
            /**
             * Board Id
             * Format: uuid
             */
            board_id: string;
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /** Revision */
            revision: number;
            /**
             * Shelf Id
             * Format: uuid
             */
            shelf_id: string;
            /**
             * Status
             * @enum {string}
             */
            status: "draft" | "trashed";
            /** Summary */
            summary: string;
            /** Title */
            title: string;
            /** Trashed At */
            trashed_at: string | null;
            /**
             * Updated At
             * Format: date-time
             */
            updated_at: string;
            /**
             * Visibility
             * @enum {string}
             */
            visibility: "public" | "members";
        };
        /** CanvasPatchForm */
        CanvasPatchForm: {
            /** Expected Revision */
            expected_revision: number;
            /**
             * Shelf Id
             * Format: uuid
             */
            shelf_id?: string;
            /** Summary */
            summary?: string;
            /** Title */
            title?: string;
            /**
             * Visibility
             * @enum {string}
             */
            visibility?: "public" | "members";
        } & (unknown | unknown | unknown | unknown);
        /** CanvasResponse */
        CanvasResponse: {
            canvas: components["schemas"]["CanvasMetadata"];
            capabilities: components["schemas"]["CanvasCapabilities"];
            /** Document Revision */
            document_revision: number;
            /**
             * View
             * @default draft
             * @constant
             */
            view: "draft";
        };
        /** CanvasRevisionForm */
        CanvasRevisionForm: {
            /** Expected Revision */
            expected_revision: number;
        };
        /** CanvasSettings */
        CanvasSettings: {
            /**
             * Background
             * @default #F8F7F4
             */
            background: string;
            /**
             * Grid
             * @default dots
             * @enum {string}
             */
            grid: "none" | "dots";
            /**
             * Height
             * @default 2100
             */
            height: number;
            /**
             * Width
             * @default 3200
             */
            width: number;
        };
        /** ChangePasswordForm */
        ChangePasswordForm: {
            /** Code */
            code: string;
            /** Password */
            password: string;
        };
        /** ConnectedEvent */
        ConnectedEvent: {
            /** Id */
            id: string;
            payload: components["schemas"]["ConnectedPayload"];
            /**
             * Ts
             * Format: date-time
             */
            ts: string;
            /**
             * @description discriminator enum property added by openapi-typescript
             * @enum {string}
             */
            type: "connected";
            /**
             * Version
             * @default v1
             */
            version: string;
        };
        /** ConnectedPayload */
        ConnectedPayload: {
            /** Channel */
            channel: string;
            /** User Id */
            user_id: number;
        };
        /** DeleteAccountCodeResponse */
        DeleteAccountCodeResponse: {
            /** Expires In */
            expires_in: number;
            /** Retry After */
            retry_after: number;
        };
        /** DeleteAccountForm */
        DeleteAccountForm: {
            /** Code */
            code: string;
            /** Email */
            email: string;
        };
        /** ForgotPasswordForm */
        ForgotPasswordForm: {
            /** Email */
            email: string;
        };
        /** ForgotPasswordResponse */
        ForgotPasswordResponse: {
            /** Message */
            message: string;
        };
        /** GradeSummary */
        GradeSummary: {
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /** Is Default */
            is_default: boolean;
            /** Name */
            name: string;
            /** Rank */
            rank: number;
        };
        /** HTTPValidationError */
        HTTPValidationError: {
            /** Detail */
            detail?: components["schemas"]["ValidationError"][];
        };
        /** HealthCheckResult */
        HealthCheckResult: {
            /**
             * Status
             * @constant
             */
            status: "ok";
        };
        /** InboxChangedEvent */
        InboxChangedEvent: {
            /** Id */
            id: string;
            /** Payload */
            payload: {
                [key: string]: unknown;
            };
            /**
             * Ts
             * Format: date-time
             */
            ts: string;
            /**
             * @description discriminator enum property added by openapi-typescript
             * @enum {string}
             */
            type: "inbox.changed";
            /**
             * Version
             * @default v1
             */
            version: string;
        };
        /** InboxErrorDetail */
        InboxErrorDetail: {
            /** Details */
            details?: {
                [key: string]: unknown;
            } | null;
            /**
             * Error
             * @example INBOX_NOT_FOUND
             * @enum {string}
             */
            error: "INBOX_NOT_FOUND";
            /** Message */
            message: string;
        };
        /** InboxErrorResponse */
        InboxErrorResponse: {
            detail: components["schemas"]["InboxErrorDetail"];
        };
        /** InboxItem */
        InboxItem: {
            /** Action Path */
            action_path: string | null;
            /** Body */
            body: string;
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
            /** Id */
            id: number;
            /** Kind */
            kind: string;
            /** Read At */
            read_at: string | null;
            /** Title */
            title: string;
        };
        /** InboxPage */
        InboxPage: {
            /** Items */
            items: components["schemas"]["InboxItem"][];
            /** Page */
            page: number;
            /** Page Size */
            page_size: number;
            summary: components["schemas"]["InboxSummary"];
            /** Total */
            total: number;
        };
        /** InboxReadAllForm */
        InboxReadAllForm: {
            /** Through Id */
            through_id: number;
        };
        /** InboxSelectionForm */
        InboxSelectionForm: {
            /** Notification Ids */
            notification_ids: number[];
        };
        /** InboxSummary */
        InboxSummary: {
            /** Latest Id */
            latest_id: number;
            /** Unread Count */
            unread_count: number;
        };
        /** InquiryCreate */
        InquiryCreate: {
            /** Body */
            body: string;
            /**
             * Request Id
             * Format: uuid
             */
            request_id: string;
            /** Subject */
            subject: string;
        };
        /** InquiryDetail */
        InquiryDetail: {
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
            /** Id */
            id: number;
            /** Messages */
            messages: components["schemas"]["InquiryMessageItem"][];
            /** Requester Email */
            requester_email: string;
            /** Requester Name */
            requester_name: string;
            status: components["schemas"]["InquiryStatus"];
            /** Subject */
            subject: string;
            /**
             * Updated At
             * Format: date-time
             */
            updated_at: string;
        };
        /** InquiryErrorDetail */
        InquiryErrorDetail: {
            /** Details */
            details?: {
                [key: string]: unknown;
            } | null;
            /**
             * Error
             * @example INQUIRY_NOT_FOUND
             * @enum {string}
             */
            error: "INQUIRY_NOT_FOUND" | "INQUIRY_CLOSED" | "INQUIRY_THREAD_FULL";
            /** Message */
            message: string;
        };
        /** InquiryErrorResponse */
        InquiryErrorResponse: {
            detail: components["schemas"]["InquiryErrorDetail"];
        };
        /** InquiryItem */
        InquiryItem: {
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
            /** Id */
            id: number;
            /** Requester Email */
            requester_email: string;
            /** Requester Name */
            requester_name: string;
            status: components["schemas"]["InquiryStatus"];
            /** Subject */
            subject: string;
            /**
             * Updated At
             * Format: date-time
             */
            updated_at: string;
        };
        /** InquiryMessageItem */
        InquiryMessageItem: {
            /** Author Role */
            author_role: string;
            /** Body */
            body: string;
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
            /** Id */
            id: number;
        };
        /** InquiryPage */
        InquiryPage: {
            /** Items */
            items: components["schemas"]["InquiryItem"][];
            /** Page */
            page: number;
            /** Page Size */
            page_size: number;
            /** Total */
            total: number;
        };
        /** InquiryReply */
        InquiryReply: {
            /** Body */
            body: string;
            /**
             * Request Id
             * Format: uuid
             */
            request_id: string;
        };
        /**
         * InquiryStatus
         * @enum {string}
         */
        InquiryStatus: "open" | "in_progress" | "closed";
        /** InquiryStatusForm */
        InquiryStatusForm: {
            status: components["schemas"]["InquiryStatus"];
        };
        /** IntegrationCheck */
        IntegrationCheck: {
            /**
             * Checked At
             * Format: date-time
             */
            checked_at: string;
            /** Latency Ms */
            latency_ms?: number | null;
            /**
             * Status
             * @enum {string}
             */
            status: "ok" | "failed" | "timeout" | "disabled";
        };
        /** InterestAdminResponse */
        InterestAdminResponse: {
            /** Active */
            active: boolean;
            /** Aliases */
            aliases?: string[];
            /** Id */
            id: string;
            /** Name En */
            name_en: string;
            /** Name Ko */
            name_ko: string;
            /**
             * Sort Order
             * @default 1000
             */
            sort_order: number;
        };
        /** InterestCatalogResponse */
        InterestCatalogResponse: {
            /** Items */
            items: components["schemas"]["InterestResponse"][];
        };
        /** InterestCreateForm */
        InterestCreateForm: {
            /** Aliases */
            aliases?: string[];
            /** Id */
            id: string;
            /** Name En */
            name_en: string;
            /** Name Ko */
            name_ko: string;
            /**
             * Sort Order
             * @default 1000
             */
            sort_order: number;
        };
        /** InterestResponse */
        InterestResponse: {
            /** Aliases */
            aliases?: string[];
            /** Id */
            id: string;
            /** Name En */
            name_en: string;
            /** Name Ko */
            name_ko: string;
        };
        /** InterestUpdateForm */
        InterestUpdateForm: {
            /** Active */
            active?: boolean | null;
            /** Aliases */
            aliases?: string[] | null;
            /** Name En */
            name_en?: string | null;
            /** Name Ko */
            name_ko?: string | null;
            /** Sort Order */
            sort_order?: number | null;
        };
        /** InternalErrorResponse */
        InternalErrorResponse: {
            /**
             * Error
             * @constant
             */
            error: "INTERNAL_ERROR";
            /** Message */
            message: string;
        };
        /** KeyboardShortcuts */
        KeyboardShortcuts: {
            /** Openprofile */
            openProfile?: string[] | null;
            /** Opensettings */
            openSettings: string[];
            /** Togglesidebar */
            toggleSidebar: string[];
        };
        /** LoginForm */
        LoginForm: {
            /** Email */
            email: string;
            /** Password */
            password: string;
            /**
             * Remember Me
             * @default false
             */
            remember_me: boolean;
        };
        /** LoginResponse */
        LoginResponse: {
            /** Access Token */
            access_token: string;
            /** Refresh Token */
            refresh_token: string;
            /**
             * Token Type
             * @default bearer
             */
            token_type: string;
            user: components["schemas"]["UserResponse"];
        };
        /** MembershipSummary */
        MembershipSummary: {
            /**
             * Grade Id
             * Format: uuid
             */
            grade_id: string;
            /** Grade Name */
            grade_name: string;
            /**
             * Role
             * @enum {string}
             */
            role: "owner" | "admin" | "moderator" | "member";
            /**
             * Status
             * @enum {string}
             */
            status: "active" | "pending" | "suspended" | "banned";
        };
        /**
         * OAuthProvider
         * @enum {string}
         */
        OAuthProvider: "google" | "github";
        /** OAuthProviderPublicConfig */
        OAuthProviderPublicConfig: {
            provider: components["schemas"]["OAuthProvider"];
            /**
             * Start Path
             * @description Backend endpoint path to start OAuth login.
             */
            start_path: string;
        };
        /** OAuthProvidersResponse */
        OAuthProvidersResponse: {
            /** Providers */
            providers: components["schemas"]["OAuthProviderPublicConfig"][];
        };
        /** PingEvent */
        PingEvent: {
            /** Id */
            id: string;
            /** Payload */
            payload: {
                [key: string]: unknown;
            };
            /**
             * Ts
             * Format: date-time
             */
            ts: string;
            /**
             * @description discriminator enum property added by openapi-typescript
             * @enum {string}
             */
            type: "ping";
            /**
             * Version
             * @default v1
             */
            version: string;
        };
        /** PolicyAuditChange */
        PolicyAuditChange: {
            after: components["schemas"]["ShelfPolicyActions"];
            before: components["schemas"]["ShelfPolicyActions"];
            /** Shelf Id */
            shelf_id: string | null;
        };
        /** PolicyChangeForm */
        PolicyChangeForm: {
            /** Expected Revision */
            expected_revision: number;
            /** Reason */
            reason: string;
        };
        /** ReadinessResponse */
        ReadinessResponse: {
            /** Checks */
            checks: {
                [key: string]: string;
            };
            /**
             * Status
             * @enum {string}
             */
            status: "ok" | "degraded";
        };
        /** RealtimeEvent */
        RealtimeEvent: {
            /** Id */
            id: string;
            /** Payload */
            payload: {
                [key: string]: unknown;
            };
            /**
             * Ts
             * Format: date-time
             */
            ts: string;
            /** Type */
            type: string;
            /**
             * Version
             * @default v1
             */
            version: string;
        };
        /** RealtimeStreamEvent */
        RealtimeStreamEvent:
            | components["schemas"]["ConnectedEvent"]
            | components["schemas"]["PingEvent"]
            | components["schemas"]["APIKeyEvent"]
            | components["schemas"]["InboxChangedEvent"];
        /** RefreshResponse */
        RefreshResponse: {
            /** Access Token */
            access_token: string;
            /** Refresh Token */
            refresh_token: string;
            /**
             * Token Type
             * @default bearer
             */
            token_type: string;
        };
        /** ResendVerificationForm */
        ResendVerificationForm: {
            /** Email */
            email: string;
        };
        /** ResendVerificationResponse */
        ResendVerificationResponse: {
            /** Message */
            message: string;
        };
        /** ResetPasswordForm */
        ResetPasswordForm: {
            /** Password */
            password: string;
            /** Token */
            token: string;
        };
        /** ResetPasswordResponse */
        ResetPasswordResponse: {
            /** Message */
            message: string;
        };
        /** ShelfAuditChange */
        ShelfAuditChange: {
            /** After */
            after: components["schemas"]["ShelfState"][];
            /** Before */
            before: components["schemas"]["ShelfState"][];
            policies_after?: components["schemas"]["ShelfPolicyActions"] | null;
            policies_before?: components["schemas"]["ShelfPolicyActions"] | null;
        };
        /** ShelfCreateForm */
        ShelfCreateForm: {
            /**
             * Classification
             * @default manual
             * @constant
             */
            classification: "manual";
            /**
             * Description
             * @default
             */
            description: string;
            /** Expected Revision */
            expected_revision: number;
            /**
             * Icon
             * @default messages-square
             */
            icon: string;
            /**
             * Is Visible
             * @default true
             */
            is_visible: boolean;
            /** Name */
            name: string;
            /**
             * Purpose
             * @default general
             * @enum {string}
             */
            purpose: "general" | "notice";
            /** Reason */
            reason: string;
            /** Slug */
            slug: string;
        };
        /** ShelfDetail */
        ShelfDetail: {
            /**
             * Board Id
             * Format: uuid
             */
            board_id: string;
            /** Capabilities */
            capabilities: {
                [key: string]: boolean;
            };
            /**
             * Classification
             * @constant
             */
            classification: "manual";
            /** Description */
            description: string;
            /** Icon */
            icon: string;
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /** Is Default */
            is_default: boolean;
            /** Is Visible */
            is_visible: boolean;
            /** Name */
            name: string;
            /**
             * Purpose
             * @enum {string}
             */
            purpose: "general" | "notice";
            /** Slug */
            slug: string;
            /** Sort Order */
            sort_order: number;
        };
        /** ShelfErrorDetail */
        ShelfErrorDetail: {
            /** Details */
            details?: {
                [key: string]: unknown;
            } | null;
            /**
             * Error
             * @example SHELF_NOT_FOUND
             * @enum {string}
             */
            error:
                | "SHELF_NOT_EMPTY"
                | "SHELF_NOT_FOUND"
                | "SHELF_SLUG_TAKEN"
                | "SHELF_LIMIT_REACHED"
                | "SHELF_PROTECTED"
                | "SHELF_INVALID_ORDER"
                | "SHELF_INVALID_POLICY";
            /** Message */
            message: string;
        };
        /** ShelfErrorResponse */
        ShelfErrorResponse: {
            detail: components["schemas"]["ShelfErrorDetail"];
        };
        /** ShelfOrderForm */
        ShelfOrderForm: {
            /** Expected Revision */
            expected_revision: number;
            /** Reason */
            reason: string;
            /** Shelf Ids */
            shelf_ids: string[];
        };
        /** ShelfPatchForm */
        ShelfPatchForm: {
            /**
             * Classification
             * @constant
             */
            classification?: "manual";
            /** Description */
            description?: string;
            /** Expected Revision */
            expected_revision: number;
            /** Icon */
            icon?: string;
            /** Is Visible */
            is_visible?: boolean;
            /** Name */
            name?: string;
            /**
             * Purpose
             * @enum {string}
             */
            purpose?: "general" | "notice";
            /** Reason */
            reason: string;
            /** Slug */
            slug?: string;
        } & (
            | {
                  /** Name */
                  name: string;
              }
            | {
                  /** Slug */
                  slug: string;
              }
            | {
                  /** Description */
                  description: string;
              }
            | {
                  /** Icon */
                  icon: string;
              }
            | {
                  /**
                   * Purpose
                   * @enum {string}
                   */
                  purpose: "general" | "notice";
              }
            | {
                  /**
                   * Classification
                   * @constant
                   */
                  classification: "manual";
              }
            | {
                  /** Is Visible */
                  is_visible: boolean;
              }
        );
        /** ShelfPoliciesForm */
        ShelfPoliciesForm: {
            actions: components["schemas"]["ShelfPolicyActions"];
            /** Expected Revision */
            expected_revision: number;
            /** Reason */
            reason: string;
        };
        /** ShelfPoliciesResponse */
        ShelfPoliciesResponse: {
            actions: components["schemas"]["ShelfPolicyActions"];
            /**
             * Board Id
             * Format: uuid
             */
            board_id: string;
            /** Board Revision */
            board_revision: number;
            effective_actions: components["schemas"]["BoardPolicyActions"];
            /**
             * Shelf Id
             * Format: uuid
             */
            shelf_id: string;
        };
        /** ShelfPolicyActions */
        ShelfPolicyActions: {
            create_canvas: components["schemas"]["ActionPolicy"] | null;
            create_comment: components["schemas"]["ActionPolicy"] | null;
            react: components["schemas"]["ActionPolicy"] | null;
            read_canvas: components["schemas"]["ActionPolicy"] | null;
        };
        /** ShelfResponse */
        ShelfResponse: {
            /** Board Revision */
            board_revision: number;
            shelf: components["schemas"]["ShelfDetail"];
        };
        /** ShelfState */
        ShelfState: {
            /**
             * Classification
             * @constant
             */
            classification: "manual";
            /** Description */
            description: string;
            /** Icon */
            icon: string;
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /** Is Default */
            is_default: boolean;
            /** Is Visible */
            is_visible: boolean;
            /** Name */
            name: string;
            /**
             * Purpose
             * @enum {string}
             */
            purpose: "general" | "notice";
            /** Slug */
            slug: string;
            /** Sort Order */
            sort_order: number;
        };
        /** ShelfSummary */
        ShelfSummary: {
            /** Capabilities */
            capabilities: {
                [key: string]: boolean;
            };
            /**
             * Classification
             * @constant
             */
            classification: "manual";
            /** Description */
            description: string;
            /** Icon */
            icon: string;
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /** Is Default */
            is_default: boolean;
            /** Name */
            name: string;
            /**
             * Purpose
             * @enum {string}
             */
            purpose: "general" | "notice";
            /** Slug */
            slug: string;
            /** Sort Order */
            sort_order: number;
        };
        /** ShelvesResponse */
        ShelvesResponse: {
            /** Board Revision */
            board_revision: number;
            /** Items */
            items: components["schemas"]["ShelfDetail"][];
        };
        /** SignupForm */
        SignupForm: {
            /** Email */
            email: string;
            /** Name */
            name: string;
            /** Password */
            password: string;
        };
        /** StartupCheck */
        StartupCheck: {
            /** Checked At */
            checked_at?: string | null;
            /**
             * Status
             * @enum {string}
             */
            status: "ok" | "configured" | "disabled" | "unverified";
        };
        /** UpdateProfileForm */
        UpdateProfileForm: {
            /** Bio */
            bio?: string | null;
            /**
             * Handle
             * @description Unique lowercase @handle: 2-24 Latin/Korean letters, digits or underscores; null clears it.
             */
            handle?: string | null;
            /** Interests */
            interests?: string[] | null;
            keyboard_shortcuts?: components["schemas"]["KeyboardShortcuts"] | null;
            /**
             * Location
             * @description Pinned country:region ID selected from the location catalog, or null.
             */
            location?: string | null;
            /** Name */
            name?: string | null;
            /**
             * Profile Image Url
             * @deprecated
             * @description Use PUT/DELETE /auth/me/photo; legacy PATCH photo writes are rejected.
             */
            profile_image_url?: string | null;
        };
        /** UserResponse */
        UserResponse: {
            /** Bio */
            bio?: string | null;
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
            /** Email */
            email: string;
            /** Handle */
            handle?: string | null;
            /**
             * Has Password
             * @default false
             */
            has_password: boolean;
            /** Id */
            id: number;
            /** Interests */
            interests?: string[];
            /** Is Verified */
            is_verified: boolean;
            keyboard_shortcuts?: components["schemas"]["KeyboardShortcuts"] | null;
            /** Location */
            location?: string | null;
            /** Name */
            name: string;
            /** Oauth Providers */
            oauth_providers?: string[];
            /** Profile Image Url */
            profile_image_url?: string | null;
            role: components["schemas"]["UserRole"];
        };
        /**
         * UserRole
         * @enum {string}
         */
        UserRole: "user" | "admin" | "manager";
        /** UserRoleStatsResponse */
        UserRoleStatsResponse: {
            /** Active Users */
            active_users: number;
            /** Admin Users */
            admin_users: number;
            /**
             * Manager Users
             * @default 0
             */
            manager_users: number;
            /** Total Users */
            total_users: number;
        };
        /** ValidationError */
        ValidationError: {
            /** Context */
            ctx?: Record<string, never>;
            /** Input */
            input?: unknown;
            /** Location */
            loc: (string | number)[];
            /** Message */
            msg: string;
            /** Error Type */
            type: string;
        };
        /** VerifyAccountCodeForm */
        VerifyAccountCodeForm: {
            /** Code */
            code: string;
        };
        /** VerifyEmailForm */
        VerifyEmailForm: {
            /** Token */
            token: string;
        };
        /** VerifyEmailResponse */
        VerifyEmailResponse: {
            /** Message */
            message: string;
            user: components["schemas"]["UserResponse"];
        };
    };
    responses: never;
    parameters: never;
    requestBodies: never;
    headers: never;
    pathItems: never;
}
export type $defs = Record<string, never>;
export interface operations {
    demo_status_api_v1_admin_demo_status_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AdminStatusResponse"];
                };
            };
            /** @description Not Found */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "ADMIN_DEMO_DISABLED",
                     *         "message": "Demo is not available."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["AdminErrorResponse"];
                };
            };
            /** @description Unexpected server error */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["InternalErrorResponse"];
                };
            };
            /** @description Service Unavailable */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "ADMIN_DEMO_FAILED",
                     *         "message": "Unable to load demo data."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["AdminErrorResponse"];
                };
            };
        };
    };
    demo_users_api_v1_admin_demo_users_get: {
        parameters: {
            query?: {
                page?: number;
                page_size?: number;
                search?: string;
                role?: components["schemas"]["UserRole"] | null;
                is_active?: boolean | null;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AdminUserListResponse"];
                };
            };
            /** @description Not Found */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "ADMIN_DEMO_DISABLED",
                     *         "message": "Demo is not available."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["AdminErrorResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
            /** @description Unexpected server error */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["InternalErrorResponse"];
                };
            };
            /** @description Service Unavailable */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "ADMIN_DEMO_FAILED",
                     *         "message": "Unable to load demo data."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["AdminErrorResponse"];
                };
            };
        };
    };
    status_api_v1_admin_status_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AdminStatusResponse"];
                };
            };
            /** @description Unauthorized */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"];
                };
            };
            /** @description Forbidden */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"];
                };
            };
            /** @description Not Found */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "USER_NOT_FOUND",
                     *         "message": "User not found."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["AuthErrorResponse"];
                };
            };
            /** @description Unexpected server error */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["InternalErrorResponse"];
                };
            };
            /** @description Service Unavailable */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "ADMIN_STATUS_FAILED",
                     *         "message": "Unable to inspect server status."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["AdminErrorResponse"];
                };
            };
        };
    };
    list_api_keys_api_v1_api_keys_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIKeysResponse"];
                };
            };
            /** @description Unauthorized */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"];
                };
            };
            /** @description Forbidden */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"];
                };
            };
            /** @description Not Found */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "USER_NOT_FOUND",
                     *         "message": "User not found."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["AuthErrorResponse"];
                };
            };
            /** @description Unexpected server error */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["InternalErrorResponse"];
                };
            };
        };
    };
    create_api_key_api_v1_api_keys_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["APIKeyCreateForm"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIKeyCreateResponse"];
                };
            };
            /** @description Unauthorized */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"];
                };
            };
            /** @description Forbidden */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"];
                };
            };
            /** @description Not Found */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "USER_NOT_FOUND",
                     *         "message": "User not found."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["AuthErrorResponse"];
                };
            };
            /** @description Conflict */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "API_KEY_NAME_ALREADY_EXISTS",
                     *         "message": "API key name already exists."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["APIKeyErrorResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
            /** @description Internal Server Error */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "API_KEY_CREATE_FAILED",
                     *         "message": "Failed to create API key."
                     *       }
                     *     }
                     */
                    "application/json":
                        | components["schemas"]["APIKeyErrorResponse"]
                        | components["schemas"]["InternalErrorResponse"];
                };
            };
        };
    };
    delete_api_key_api_v1_api_keys__api_key_id__delete: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                api_key_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIKeyResponse"];
                };
            };
            /** @description Unauthorized */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"];
                };
            };
            /** @description Forbidden */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"];
                };
            };
            /** @description Not Found */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
            /** @description Unexpected server error */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["InternalErrorResponse"];
                };
            };
        };
    };
    update_api_key_status_api_v1_api_keys__api_key_id__status_patch: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                api_key_id: number;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["APIKeyStatusUpdateForm"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIKeyResponse"];
                };
            };
            /** @description Unauthorized */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"];
                };
            };
            /** @description Forbidden */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"];
                };
            };
            /** @description Not Found */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
            /** @description Internal Server Error */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "API_KEY_UPDATE_FAILED",
                     *         "message": "Failed to update API key state."
                     *       }
                     *     }
                     */
                    "application/json":
                        | components["schemas"]["APIKeyErrorResponse"]
                        | components["schemas"]["InternalErrorResponse"];
                };
            };
        };
    };
    admin_user_role_stats_api_v1_auth_admin_user_role_stats_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["UserRoleStatsResponse"];
                };
            };
            /** @description Unauthorized */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"];
                };
            };
            /** @description Forbidden */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"];
                };
            };
            /** @description Not Found */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "USER_NOT_FOUND",
                     *         "message": "User not found."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["AuthErrorResponse"];
                };
            };
            /** @description Unexpected server error */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["InternalErrorResponse"];
                };
            };
        };
    };
    admin_users_api_v1_auth_admin_users_get: {
        parameters: {
            query?: {
                page?: number;
                page_size?: number;
                search?: string;
                role?: components["schemas"]["UserRole"] | null;
                is_active?: boolean | null;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AdminUserListResponse"];
                };
            };
            /** @description Unauthorized */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"];
                };
            };
            /** @description Forbidden */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"];
                };
            };
            /** @description Not Found */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "USER_NOT_FOUND",
                     *         "message": "User not found."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["AuthErrorResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
            /** @description Internal Server Error */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "ADMIN_USERS_FAILED",
                     *         "message": "Failed to load the user directory."
                     *       }
                     *     }
                     */
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["InternalErrorResponse"];
                };
            };
        };
    };
    forgot_password_api_v1_auth_forgot_password_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["ForgotPasswordForm"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ForgotPasswordResponse"];
                };
            };
            /** @description Forbidden */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "LOGIN_DISABLED",
                     *         "message": "Login is currently disabled."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["AuthErrorResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
            /** @description Unexpected server error */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["InternalErrorResponse"];
                };
            };
        };
    };
    login_api_v1_auth_login_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["LoginForm"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    /** @description Two separate Set-Cookie headers: template_refresh_token and template_refresh_sid; HttpOnly, Path=/; HTTPS uses Secure and SameSite=None, HTTP uses SameSite=Lax. Persistent expiry is set only with remember_me=true. */
                    "Set-Cookie"?: string;
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["LoginResponse"];
                };
            };
            /** @description Unauthorized */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "INVALID_CREDENTIALS",
                     *         "message": "Incorrect email or password."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["AuthErrorResponse"];
                };
            };
            /** @description Forbidden */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "LOGIN_DISABLED",
                     *         "message": "Login is currently disabled."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["AuthErrorResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
            /** @description Locked */
            423: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "details": {
                     *           "remaining_seconds": 120
                     *         },
                     *         "error": "ACCOUNT_LOCKED",
                     *         "message": "Account is temporarily locked."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["AuthErrorResponse"];
                };
            };
            /** @description Unexpected server error */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["InternalErrorResponse"];
                };
            };
        };
    };
    logout_api_v1_auth_logout_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    /** @description Separate expiry headers for template_refresh_token and template_refresh_sid at Path=/. */
                    "Set-Cookie"?: string;
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: string;
                    };
                };
            };
            /** @description Unauthorized */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"];
                };
            };
            /** @description Forbidden */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"];
                };
            };
            /** @description Not Found */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "USER_NOT_FOUND",
                     *         "message": "User not found."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["AuthErrorResponse"];
                };
            };
            /** @description Unexpected server error */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["InternalErrorResponse"];
                };
            };
        };
    };
    me_api_v1_auth_me_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["UserResponse"];
                };
            };
            /** @description Unauthorized */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"];
                };
            };
            /** @description Forbidden */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"];
                };
            };
            /** @description Not Found */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "USER_NOT_FOUND",
                     *         "message": "User not found."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["AuthErrorResponse"];
                };
            };
            /** @description Unexpected server error */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["InternalErrorResponse"];
                };
            };
        };
    };
    delete_me_api_v1_auth_me_delete: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["DeleteAccountForm"];
            };
        };
        responses: {
            /** @description Successful Response */
            204: {
                headers: {
                    [name: string]: unknown;
                };
                content?: never;
            };
            /** @description Bad Request */
            400: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "ACCOUNT_DELETE_CODE_INVALID",
                     *         "message": "The deletion code is invalid, expired or locked. Request a new code after the cooldown."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["AuthErrorResponse"];
                };
            };
            /** @description Unauthorized */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "INVALID_TOKEN",
                     *         "message": "Invalid refresh token."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["AuthErrorResponse"];
                };
            };
            /** @description Forbidden */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "INSUFFICIENT_ROLE",
                     *         "message": "User does not have enough permissions."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["AuthErrorResponse"];
                };
            };
            /** @description Not Found */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "USER_NOT_FOUND",
                     *         "message": "User not found."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["AuthErrorResponse"];
                };
            };
            /** @description Conflict */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "ACCOUNT_BILLING_REVIEW_REQUIRED",
                     *         "message": "Contact the operator to reconcile subscriptions before deleting this account."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["AuthErrorResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
            /** @description Internal Server Error */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "ACCOUNT_DELETE_FAILED",
                     *         "message": "Failed to delete account."
                     *       }
                     *     }
                     */
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["InternalErrorResponse"];
                };
            };
        };
    };
    update_me_api_v1_auth_me_patch: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["UpdateProfileForm"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["UserResponse"];
                };
            };
            /** @description Unauthorized */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"];
                };
            };
            /** @description Forbidden */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"];
                };
            };
            /** @description Not Found */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "USER_NOT_FOUND",
                     *         "message": "User not found."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["AuthErrorResponse"];
                };
            };
            /** @description Conflict */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "HANDLE_ALREADY_EXISTS",
                     *         "message": "This profile handle is already in use."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["AuthErrorResponse"];
                };
            };
            /** @description Unprocessable Content */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "INTEREST_NOT_AVAILABLE",
                     *         "message": "Select an active official interest."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["AuthErrorResponse"];
                };
            };
            /** @description Internal Server Error */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "PROFILE_UPDATE_FAILED",
                     *         "message": "Failed to update profile."
                     *       }
                     *     }
                     */
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["InternalErrorResponse"];
                };
            };
        };
    };
    request_deletion_code_api_v1_auth_me_deletion_code_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["DeleteAccountCodeResponse"];
                };
            };
            /** @description Unauthorized */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "INVALID_TOKEN",
                     *         "message": "Invalid refresh token."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["AuthErrorResponse"];
                };
            };
            /** @description Forbidden */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "INSUFFICIENT_ROLE",
                     *         "message": "User does not have enough permissions."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["AuthErrorResponse"];
                };
            };
            /** @description Not Found */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "USER_NOT_FOUND",
                     *         "message": "User not found."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["AuthErrorResponse"];
                };
            };
            /** @description Too Many Requests */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "ACCOUNT_DELETE_CODE_THROTTLED",
                     *         "message": "Wait before requesting another deletion code."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["AuthErrorResponse"];
                };
            };
            /** @description Unexpected server error */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["InternalErrorResponse"];
                };
            };
            /** @description Service Unavailable */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "ACCOUNT_DELETE_CODE_SEND_FAILED",
                     *         "message": "Unable to queue the deletion code. Try again later."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["AuthErrorResponse"];
                };
            };
        };
    };
    verify_deletion_code_api_v1_auth_me_deletion_code_verify_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["VerifyAccountCodeForm"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ResetPasswordResponse"];
                };
            };
            /** @description Bad Request */
            400: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "ACCOUNT_DELETE_CODE_INVALID",
                     *         "message": "The deletion code is invalid, expired or locked. Request a new code after the cooldown."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["AuthErrorResponse"];
                };
            };
            /** @description Unauthorized */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"];
                };
            };
            /** @description Forbidden */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"];
                };
            };
            /** @description Not Found */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "USER_NOT_FOUND",
                     *         "message": "User not found."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["AuthErrorResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
            /** @description Internal Server Error */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "ACCOUNT_DELETE_FAILED",
                     *         "message": "Failed to delete account."
                     *       }
                     *     }
                     */
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["InternalErrorResponse"];
                };
            };
        };
    };
    change_password_api_v1_auth_me_password_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["ChangePasswordForm"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ResetPasswordResponse"];
                };
            };
            /** @description Bad Request */
            400: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "PASSWORD_CHANGE_CODE_INVALID",
                     *         "message": "The password change code is invalid, expired or locked."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["AuthErrorResponse"];
                };
            };
            /** @description Unauthorized */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"];
                };
            };
            /** @description Forbidden */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"];
                };
            };
            /** @description Not Found */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "USER_NOT_FOUND",
                     *         "message": "User not found."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["AuthErrorResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
            /** @description Too Many Requests */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "PASSWORD_CHANGE_CODE_THROTTLED",
                     *         "message": "Wait before requesting another password change code."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["AuthErrorResponse"];
                };
            };
            /** @description Unexpected server error */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["InternalErrorResponse"];
                };
            };
            /** @description Service Unavailable */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "PASSWORD_CHANGE_CODE_SEND_FAILED",
                     *         "message": "Unable to queue the password change code."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["AuthErrorResponse"];
                };
            };
        };
    };
    request_password_change_code_api_v1_auth_me_password_code_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["DeleteAccountCodeResponse"];
                };
            };
            /** @description Bad Request */
            400: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "PASSWORD_CHANGE_CODE_INVALID",
                     *         "message": "The password change code is invalid, expired or locked."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["AuthErrorResponse"];
                };
            };
            /** @description Unauthorized */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"];
                };
            };
            /** @description Forbidden */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"];
                };
            };
            /** @description Not Found */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "USER_NOT_FOUND",
                     *         "message": "User not found."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["AuthErrorResponse"];
                };
            };
            /** @description Too Many Requests */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "PASSWORD_CHANGE_CODE_THROTTLED",
                     *         "message": "Wait before requesting another password change code."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["AuthErrorResponse"];
                };
            };
            /** @description Unexpected server error */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["InternalErrorResponse"];
                };
            };
            /** @description Service Unavailable */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "PASSWORD_CHANGE_CODE_SEND_FAILED",
                     *         "message": "Unable to queue the password change code."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["AuthErrorResponse"];
                };
            };
        };
    };
    verify_password_change_code_api_v1_auth_me_password_code_verify_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["VerifyAccountCodeForm"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ResetPasswordResponse"];
                };
            };
            /** @description Bad Request */
            400: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "PASSWORD_CHANGE_CODE_INVALID",
                     *         "message": "The password change code is invalid, expired or locked."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["AuthErrorResponse"];
                };
            };
            /** @description Unauthorized */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"];
                };
            };
            /** @description Forbidden */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"];
                };
            };
            /** @description Not Found */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "USER_NOT_FOUND",
                     *         "message": "User not found."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["AuthErrorResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
            /** @description Too Many Requests */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "PASSWORD_CHANGE_CODE_THROTTLED",
                     *         "message": "Wait before requesting another password change code."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["AuthErrorResponse"];
                };
            };
            /** @description Unexpected server error */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["InternalErrorResponse"];
                };
            };
            /** @description Service Unavailable */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "PASSWORD_CHANGE_CODE_SEND_FAILED",
                     *         "message": "Unable to queue the password change code."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["AuthErrorResponse"];
                };
            };
        };
    };
    read_profile_photo_api_v1_auth_me_photo_get: {
        parameters: {
            query?: {
                version?: string | null;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "image/webp": string;
                };
            };
            /** @description Unauthorized */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"];
                };
            };
            /** @description Forbidden */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"];
                };
            };
            /** @description Not Found */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AuthErrorResponse"];
                };
            };
            /** @description Conflict */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "PROFILE_PHOTO_CONFLICT",
                     *         "message": "Profile image changed; refresh and try again."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["AuthErrorResponse"];
                };
            };
            /** @description Content Too Large */
            413: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "PROFILE_PHOTO_TOO_LARGE",
                     *         "message": "Profile image exceeds the upload limit."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["AuthErrorResponse"];
                };
            };
            /** @description Unprocessable Content */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "PROFILE_PHOTO_INVALID",
                     *         "message": "Invalid profile image."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["AuthErrorResponse"];
                };
            };
            /** @description Internal Server Error */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "PROFILE_UPDATE_FAILED",
                     *         "message": "Failed to update profile."
                     *       }
                     *     }
                     */
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["InternalErrorResponse"];
                };
            };
            /** @description Service Unavailable */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "PROFILE_PHOTO_UNAVAILABLE",
                     *         "message": "Profile image storage is unavailable."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["AuthErrorResponse"];
                };
            };
        };
    };
    upload_profile_photo_api_v1_auth_me_photo_put: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/octet-stream": string;
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["UserResponse"];
                };
            };
            /** @description Unauthorized */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"];
                };
            };
            /** @description Forbidden */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"];
                };
            };
            /** @description Not Found */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AuthErrorResponse"];
                };
            };
            /** @description Conflict */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "PROFILE_PHOTO_CONFLICT",
                     *         "message": "Profile image changed; refresh and try again."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["AuthErrorResponse"];
                };
            };
            /** @description Content Too Large */
            413: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "PROFILE_PHOTO_TOO_LARGE",
                     *         "message": "Profile image exceeds the upload limit."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["AuthErrorResponse"];
                };
            };
            /** @description Unprocessable Content */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "PROFILE_PHOTO_INVALID",
                     *         "message": "Invalid profile image."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["AuthErrorResponse"];
                };
            };
            /** @description Internal Server Error */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "PROFILE_UPDATE_FAILED",
                     *         "message": "Failed to update profile."
                     *       }
                     *     }
                     */
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["InternalErrorResponse"];
                };
            };
            /** @description Service Unavailable */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "PROFILE_PHOTO_UNAVAILABLE",
                     *         "message": "Profile image storage is unavailable."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["AuthErrorResponse"];
                };
            };
        };
    };
    delete_profile_photo_api_v1_auth_me_photo_delete: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["UserResponse"];
                };
            };
            /** @description Unauthorized */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"];
                };
            };
            /** @description Forbidden */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"];
                };
            };
            /** @description Not Found */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AuthErrorResponse"];
                };
            };
            /** @description Conflict */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "PROFILE_PHOTO_CONFLICT",
                     *         "message": "Profile image changed; refresh and try again."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["AuthErrorResponse"];
                };
            };
            /** @description Content Too Large */
            413: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "PROFILE_PHOTO_TOO_LARGE",
                     *         "message": "Profile image exceeds the upload limit."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["AuthErrorResponse"];
                };
            };
            /** @description Unprocessable Content */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "PROFILE_PHOTO_INVALID",
                     *         "message": "Invalid profile image."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["AuthErrorResponse"];
                };
            };
            /** @description Internal Server Error */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "PROFILE_UPDATE_FAILED",
                     *         "message": "Failed to update profile."
                     *       }
                     *     }
                     */
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["InternalErrorResponse"];
                };
            };
            /** @description Service Unavailable */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "PROFILE_PHOTO_UNAVAILABLE",
                     *         "message": "Profile image storage is unavailable."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["AuthErrorResponse"];
                };
            };
        };
    };
    oauth_providers_api_v1_auth_oauth_providers_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["OAuthProvidersResponse"];
                };
            };
            /** @description Bad Request */
            400: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "OAUTH_PROVIDER_NOT_ENABLED",
                     *         "message": "The requested OAuth provider is not enabled."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["AuthErrorResponse"];
                };
            };
            /** @description Forbidden */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "LOGIN_DISABLED",
                     *         "message": "Login is currently disabled."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["AuthErrorResponse"];
                };
            };
            /** @description Internal Server Error */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "OAUTH_PROVIDER_CONFIG_INVALID",
                     *         "message": "OAuth provider configuration is invalid."
                     *       }
                     *     }
                     */
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["InternalErrorResponse"];
                };
            };
        };
    };
    oauth_callback_api_v1_auth_oauth__provider__callback_get: {
        parameters: {
            query?: {
                code?: string | null;
                state?: string | null;
                error?: string | null;
            };
            header?: never;
            path: {
                provider: components["schemas"]["OAuthProvider"];
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Success redirects to the frontend and sets refresh cookies. Provider/domain failures redirect to the frontend failure path with error query parameters. */
            307: {
                headers: {
                    /** @description Redirect destination */
                    Location?: string;
                    /** @description Two separate Set-Cookie headers: template_refresh_token and template_refresh_sid; HttpOnly, Path=/; HTTPS uses Secure and SameSite=None, HTTP uses SameSite=Lax. Persistent expiry is set only with remember_me=true. */
                    "Set-Cookie"?: string;
                    [name: string]: unknown;
                };
                content?: never;
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
            /** @description Unexpected server error */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["InternalErrorResponse"];
                };
            };
        };
    };
    oauth_start_api_v1_auth_oauth__provider__start_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                provider: components["schemas"]["OAuthProvider"];
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            307: {
                headers: {
                    /** @description Redirect destination */
                    Location?: string;
                    [name: string]: unknown;
                };
                content?: never;
            };
            /** @description Bad Request */
            400: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "OAUTH_PROVIDER_NOT_ENABLED",
                     *         "message": "The requested OAuth provider is not enabled."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["AuthErrorResponse"];
                };
            };
            /** @description Forbidden */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "LOGIN_DISABLED",
                     *         "message": "Login is currently disabled."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["AuthErrorResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
            /** @description Internal Server Error */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "OAUTH_PROVIDER_CONFIG_INVALID",
                     *         "message": "OAuth provider configuration is invalid."
                     *       }
                     *     }
                     */
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["InternalErrorResponse"];
                };
            };
        };
    };
    refresh_token_api_v1_auth_refresh_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: {
                template_refresh_token?: string;
                template_refresh_sid?: string;
            };
        };
        requestBody?: {
            content: {
                "application/json": components["schemas"]["Body_refresh_token_api_v1_auth_refresh_post"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    /** @description Two separate Set-Cookie headers: template_refresh_token and template_refresh_sid; HttpOnly, Path=/; HTTPS uses Secure and SameSite=None, HTTP uses SameSite=Lax. Persistent expiry is set only with remember_me=true. */
                    "Set-Cookie"?: string;
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["RefreshResponse"];
                };
            };
            /** @description Unauthorized */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "INVALID_TOKEN",
                     *         "message": "Invalid refresh token."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["AuthErrorResponse"];
                };
            };
            /** @description Forbidden */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "LOGIN_DISABLED",
                     *         "message": "Login is currently disabled."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["AuthErrorResponse"];
                };
            };
            /** @description Not Found */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "USER_NOT_FOUND",
                     *         "message": "User not found."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["AuthErrorResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
            /** @description Unexpected server error */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["InternalErrorResponse"];
                };
            };
        };
    };
    resend_verification_email_api_v1_auth_resend_verification_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["ResendVerificationForm"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ResendVerificationResponse"];
                };
            };
            /** @description Forbidden */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "LOGIN_DISABLED",
                     *         "message": "Login is currently disabled."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["AuthErrorResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
            /** @description Unexpected server error */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["InternalErrorResponse"];
                };
            };
        };
    };
    reset_password_api_v1_auth_reset_password_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["ResetPasswordForm"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ResetPasswordResponse"];
                };
            };
            /** @description Unauthorized */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "INVALID_TOKEN",
                     *         "message": "Invalid refresh token."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["AuthErrorResponse"];
                };
            };
            /** @description Forbidden */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "LOGIN_DISABLED",
                     *         "message": "Login is currently disabled."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["AuthErrorResponse"];
                };
            };
            /** @description Not Found */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "USER_NOT_FOUND",
                     *         "message": "User not found."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["AuthErrorResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
            /** @description Unexpected server error */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["InternalErrorResponse"];
                };
            };
        };
    };
    signup_api_v1_auth_signup_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["SignupForm"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["UserResponse"];
                };
            };
            /** @description Forbidden */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "LOGIN_DISABLED",
                     *         "message": "Login is currently disabled."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["AuthErrorResponse"];
                };
            };
            /** @description Conflict */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "EMAIL_ALREADY_EXISTS",
                     *         "message": "User with this email already exists."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["AuthErrorResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
            /** @description Internal Server Error */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "SIGNUP_FAILED",
                     *         "message": "Failed to create the user account."
                     *       }
                     *     }
                     */
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["InternalErrorResponse"];
                };
            };
        };
    };
    oauth_token_login_api_v1_auth_token_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/x-www-form-urlencoded": components["schemas"]["Body_oauth_token_login_api_v1_auth_token_post"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["LoginResponse"];
                };
            };
            /** @description Unauthorized */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "INVALID_CREDENTIALS",
                     *         "message": "Incorrect email or password."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["AuthErrorResponse"];
                };
            };
            /** @description Forbidden */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "LOGIN_DISABLED",
                     *         "message": "Login is currently disabled."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["AuthErrorResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
            /** @description Locked */
            423: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "details": {
                     *           "remaining_seconds": 120
                     *         },
                     *         "error": "ACCOUNT_LOCKED",
                     *         "message": "Account is temporarily locked."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["AuthErrorResponse"];
                };
            };
            /** @description Unexpected server error */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["InternalErrorResponse"];
                };
            };
        };
    };
    verify_email_api_v1_auth_verify_email_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["VerifyEmailForm"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["VerifyEmailResponse"];
                };
            };
            /** @description Unauthorized */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "INVALID_TOKEN",
                     *         "message": "Invalid refresh token."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["AuthErrorResponse"];
                };
            };
            /** @description Forbidden */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "LOGIN_DISABLED",
                     *         "message": "Login is currently disabled."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["AuthErrorResponse"];
                };
            };
            /** @description Not Found */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "USER_NOT_FOUND",
                     *         "message": "User not found."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["AuthErrorResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
            /** @description Unexpected server error */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["InternalErrorResponse"];
                };
            };
        };
    };
    create_card_setup_api_v1_billing_card_setups_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["BillingSetupForm"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["BillingCardSetupResponse"];
                };
            };
            /** @description Bad Request */
            400: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "BILLING_WEBHOOK_INVALID",
                     *         "message": "Invalid billing webhook."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["BillingErrorResponse"];
                };
            };
            /** @description Unauthorized */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"];
                };
            };
            /** @description Forbidden */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"];
                };
            };
            /** @description Not Found */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["BillingErrorResponse"];
                };
            };
            /** @description Conflict */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "BILLING_CHECKOUT_CONFLICT",
                     *         "message": "An existing subscription or another checkout requires attention."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["BillingErrorResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
            /** @description Unexpected server error */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["InternalErrorResponse"];
                };
            };
            /** @description Bad Gateway */
            502: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "BILLING_UNAVAILABLE",
                     *         "message": "Payment provider is temporarily unavailable."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["BillingErrorResponse"];
                };
            };
            /** @description Service Unavailable */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "BILLING_WEBHOOK_UNAVAILABLE",
                     *         "message": "Billing webhook is not configured."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["BillingErrorResponse"];
                };
            };
        };
    };
    card_setup_status_api_v1_billing_card_setups__intent_id__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                intent_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["BillingCardSetupStatus"];
                };
            };
            /** @description Bad Request */
            400: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "BILLING_WEBHOOK_INVALID",
                     *         "message": "Invalid billing webhook."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["BillingErrorResponse"];
                };
            };
            /** @description Unauthorized */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"];
                };
            };
            /** @description Forbidden */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"];
                };
            };
            /** @description Not Found */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["BillingErrorResponse"];
                };
            };
            /** @description Conflict */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "BILLING_CHECKOUT_CONFLICT",
                     *         "message": "An existing subscription or another checkout requires attention."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["BillingErrorResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
            /** @description Unexpected server error */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["InternalErrorResponse"];
                };
            };
            /** @description Bad Gateway */
            502: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "BILLING_UNAVAILABLE",
                     *         "message": "Payment provider is temporarily unavailable."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["BillingErrorResponse"];
                };
            };
            /** @description Service Unavailable */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "BILLING_WEBHOOK_UNAVAILABLE",
                     *         "message": "Billing webhook is not configured."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["BillingErrorResponse"];
                };
            };
        };
    };
    create_checkout_api_v1_billing_checkout_sessions_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["BillingCheckoutForm"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["BillingSetupResponse"];
                };
            };
            /** @description Bad Request */
            400: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "BILLING_WEBHOOK_INVALID",
                     *         "message": "Invalid billing webhook."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["BillingErrorResponse"];
                };
            };
            /** @description Unauthorized */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"];
                };
            };
            /** @description Forbidden */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"];
                };
            };
            /** @description Not Found */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["BillingErrorResponse"];
                };
            };
            /** @description Conflict */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "BILLING_CHECKOUT_CONFLICT",
                     *         "message": "An existing subscription or another checkout requires attention."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["BillingErrorResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
            /** @description Unexpected server error */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["InternalErrorResponse"];
                };
            };
            /** @description Bad Gateway */
            502: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "BILLING_UNAVAILABLE",
                     *         "message": "Payment provider is temporarily unavailable."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["BillingErrorResponse"];
                };
            };
            /** @description Service Unavailable */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "BILLING_WEBHOOK_UNAVAILABLE",
                     *         "message": "Billing webhook is not configured."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["BillingErrorResponse"];
                };
            };
        };
    };
    checkout_status_api_v1_billing_checkout_sessions__session_id__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                session_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["BillingCheckoutStatusResponse"];
                };
            };
            /** @description Bad Request */
            400: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "BILLING_WEBHOOK_INVALID",
                     *         "message": "Invalid billing webhook."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["BillingErrorResponse"];
                };
            };
            /** @description Unauthorized */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"];
                };
            };
            /** @description Forbidden */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"];
                };
            };
            /** @description Not Found */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["BillingErrorResponse"];
                };
            };
            /** @description Conflict */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "BILLING_CHECKOUT_CONFLICT",
                     *         "message": "An existing subscription or another checkout requires attention."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["BillingErrorResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
            /** @description Unexpected server error */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["InternalErrorResponse"];
                };
            };
            /** @description Bad Gateway */
            502: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "BILLING_UNAVAILABLE",
                     *         "message": "Payment provider is temporarily unavailable."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["BillingErrorResponse"];
                };
            };
            /** @description Service Unavailable */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "BILLING_WEBHOOK_UNAVAILABLE",
                     *         "message": "Billing webhook is not configured."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["BillingErrorResponse"];
                };
            };
        };
    };
    billing_config_api_v1_billing_config_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["BillingConfigResponse"];
                };
            };
            /** @description Bad Request */
            400: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "BILLING_WEBHOOK_INVALID",
                     *         "message": "Invalid billing webhook."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["BillingErrorResponse"];
                };
            };
            /** @description Unauthorized */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"];
                };
            };
            /** @description Forbidden */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"];
                };
            };
            /** @description Not Found */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["BillingErrorResponse"];
                };
            };
            /** @description Conflict */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "BILLING_CHECKOUT_CONFLICT",
                     *         "message": "An existing subscription or another checkout requires attention."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["BillingErrorResponse"];
                };
            };
            /** @description Unexpected server error */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["InternalErrorResponse"];
                };
            };
            /** @description Bad Gateway */
            502: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "BILLING_UNAVAILABLE",
                     *         "message": "Payment provider is temporarily unavailable."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["BillingErrorResponse"];
                };
            };
            /** @description Service Unavailable */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "BILLING_WEBHOOK_UNAVAILABLE",
                     *         "message": "Billing webhook is not configured."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["BillingErrorResponse"];
                };
            };
        };
    };
    billing_invoices_api_v1_billing_invoices_get: {
        parameters: {
            query?: {
                limit?: number;
                starting_after?: string | null;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["BillingInvoicesResponse"];
                };
            };
            /** @description Bad Request */
            400: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "BILLING_WEBHOOK_INVALID",
                     *         "message": "Invalid billing webhook."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["BillingErrorResponse"];
                };
            };
            /** @description Unauthorized */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"];
                };
            };
            /** @description Forbidden */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"];
                };
            };
            /** @description Not Found */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["BillingErrorResponse"];
                };
            };
            /** @description Conflict */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "BILLING_CHECKOUT_CONFLICT",
                     *         "message": "An existing subscription or another checkout requires attention."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["BillingErrorResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
            /** @description Unexpected server error */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["InternalErrorResponse"];
                };
            };
            /** @description Bad Gateway */
            502: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "BILLING_UNAVAILABLE",
                     *         "message": "Payment provider is temporarily unavailable."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["BillingErrorResponse"];
                };
            };
            /** @description Service Unavailable */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "BILLING_WEBHOOK_UNAVAILABLE",
                     *         "message": "Billing webhook is not configured."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["BillingErrorResponse"];
                };
            };
        };
    };
    invoice_detail_api_v1_billing_invoices__invoice_id__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                invoice_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["BillingInvoiceDetail"];
                };
            };
            /** @description Bad Request */
            400: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "BILLING_WEBHOOK_INVALID",
                     *         "message": "Invalid billing webhook."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["BillingErrorResponse"];
                };
            };
            /** @description Unauthorized */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"];
                };
            };
            /** @description Forbidden */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"];
                };
            };
            /** @description Not Found */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["BillingErrorResponse"];
                };
            };
            /** @description Conflict */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "BILLING_CHECKOUT_CONFLICT",
                     *         "message": "An existing subscription or another checkout requires attention."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["BillingErrorResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
            /** @description Unexpected server error */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["InternalErrorResponse"];
                };
            };
            /** @description Bad Gateway */
            502: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "BILLING_UNAVAILABLE",
                     *         "message": "Payment provider is temporarily unavailable."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["BillingErrorResponse"];
                };
            };
            /** @description Service Unavailable */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "BILLING_WEBHOOK_UNAVAILABLE",
                     *         "message": "Billing webhook is not configured."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["BillingErrorResponse"];
                };
            };
        };
    };
    list_payment_methods_api_v1_billing_payment_methods_get: {
        parameters: {
            query?: {
                method_type?: "card" | "link";
                limit?: number;
                starting_after?: string | null;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["BillingPaymentMethodsResponse"];
                };
            };
            /** @description Bad Request */
            400: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "BILLING_WEBHOOK_INVALID",
                     *         "message": "Invalid billing webhook."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["BillingErrorResponse"];
                };
            };
            /** @description Unauthorized */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"];
                };
            };
            /** @description Forbidden */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"];
                };
            };
            /** @description Not Found */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["BillingErrorResponse"];
                };
            };
            /** @description Conflict */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "BILLING_CHECKOUT_CONFLICT",
                     *         "message": "An existing subscription or another checkout requires attention."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["BillingErrorResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
            /** @description Unexpected server error */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["InternalErrorResponse"];
                };
            };
            /** @description Bad Gateway */
            502: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "BILLING_UNAVAILABLE",
                     *         "message": "Payment provider is temporarily unavailable."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["BillingErrorResponse"];
                };
            };
            /** @description Service Unavailable */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "BILLING_WEBHOOK_UNAVAILABLE",
                     *         "message": "Billing webhook is not configured."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["BillingErrorResponse"];
                };
            };
        };
    };
    manage_billing_method_api_v1_billing_payment_methods__method_id__post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                method_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["BillingMethodForm"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["BillingProfileResponse"];
                };
            };
            /** @description Bad Request */
            400: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "BILLING_WEBHOOK_INVALID",
                     *         "message": "Invalid billing webhook."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["BillingErrorResponse"];
                };
            };
            /** @description Unauthorized */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"];
                };
            };
            /** @description Forbidden */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"];
                };
            };
            /** @description Not Found */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["BillingErrorResponse"];
                };
            };
            /** @description Conflict */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "BILLING_CHECKOUT_CONFLICT",
                     *         "message": "An existing subscription or another checkout requires attention."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["BillingErrorResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
            /** @description Unexpected server error */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["InternalErrorResponse"];
                };
            };
            /** @description Bad Gateway */
            502: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "BILLING_UNAVAILABLE",
                     *         "message": "Payment provider is temporarily unavailable."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["BillingErrorResponse"];
                };
            };
            /** @description Service Unavailable */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "BILLING_WEBHOOK_UNAVAILABLE",
                     *         "message": "Billing webhook is not configured."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["BillingErrorResponse"];
                };
            };
        };
    };
    plans_api_v1_billing_plans_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["BillingPlansResponse"];
                };
            };
            /** @description Bad Request */
            400: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "BILLING_WEBHOOK_INVALID",
                     *         "message": "Invalid billing webhook."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["BillingErrorResponse"];
                };
            };
            /** @description Unauthorized */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"];
                };
            };
            /** @description Forbidden */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"];
                };
            };
            /** @description Not Found */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["BillingErrorResponse"];
                };
            };
            /** @description Conflict */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "BILLING_CHECKOUT_CONFLICT",
                     *         "message": "An existing subscription or another checkout requires attention."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["BillingErrorResponse"];
                };
            };
            /** @description Unexpected server error */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["InternalErrorResponse"];
                };
            };
            /** @description Bad Gateway */
            502: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "BILLING_UNAVAILABLE",
                     *         "message": "Payment provider is temporarily unavailable."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["BillingErrorResponse"];
                };
            };
            /** @description Service Unavailable */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "BILLING_WEBHOOK_UNAVAILABLE",
                     *         "message": "Billing webhook is not configured."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["BillingErrorResponse"];
                };
            };
        };
    };
    billing_portal_api_v1_billing_portal_sessions_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["BillingPortalForm"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["BillingSetupResponse"];
                };
            };
            /** @description Bad Request */
            400: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "BILLING_WEBHOOK_INVALID",
                     *         "message": "Invalid billing webhook."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["BillingErrorResponse"];
                };
            };
            /** @description Unauthorized */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"];
                };
            };
            /** @description Forbidden */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"];
                };
            };
            /** @description Not Found */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["BillingErrorResponse"];
                };
            };
            /** @description Conflict */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "BILLING_CHECKOUT_CONFLICT",
                     *         "message": "An existing subscription or another checkout requires attention."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["BillingErrorResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
            /** @description Unexpected server error */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["InternalErrorResponse"];
                };
            };
            /** @description Bad Gateway */
            502: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "BILLING_UNAVAILABLE",
                     *         "message": "Payment provider is temporarily unavailable."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["BillingErrorResponse"];
                };
            };
            /** @description Service Unavailable */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "BILLING_WEBHOOK_UNAVAILABLE",
                     *         "message": "Billing webhook is not configured."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["BillingErrorResponse"];
                };
            };
        };
    };
    billing_profile_api_v1_billing_profile_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["BillingProfileResponse"];
                };
            };
            /** @description Bad Request */
            400: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "BILLING_WEBHOOK_INVALID",
                     *         "message": "Invalid billing webhook."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["BillingErrorResponse"];
                };
            };
            /** @description Unauthorized */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"];
                };
            };
            /** @description Forbidden */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"];
                };
            };
            /** @description Not Found */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["BillingErrorResponse"];
                };
            };
            /** @description Conflict */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "BILLING_CHECKOUT_CONFLICT",
                     *         "message": "An existing subscription or another checkout requires attention."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["BillingErrorResponse"];
                };
            };
            /** @description Unexpected server error */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["InternalErrorResponse"];
                };
            };
            /** @description Bad Gateway */
            502: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "BILLING_UNAVAILABLE",
                     *         "message": "Payment provider is temporarily unavailable."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["BillingErrorResponse"];
                };
            };
            /** @description Service Unavailable */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "BILLING_WEBHOOK_UNAVAILABLE",
                     *         "message": "Billing webhook is not configured."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["BillingErrorResponse"];
                };
            };
        };
    };
    update_billing_profile_api_v1_billing_profile_put: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["BillingProfileForm"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["BillingProfileResponse"];
                };
            };
            /** @description Bad Request */
            400: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "BILLING_WEBHOOK_INVALID",
                     *         "message": "Invalid billing webhook."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["BillingErrorResponse"];
                };
            };
            /** @description Unauthorized */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"];
                };
            };
            /** @description Forbidden */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"];
                };
            };
            /** @description Not Found */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["BillingErrorResponse"];
                };
            };
            /** @description Conflict */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "BILLING_CHECKOUT_CONFLICT",
                     *         "message": "An existing subscription or another checkout requires attention."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["BillingErrorResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
            /** @description Unexpected server error */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["InternalErrorResponse"];
                };
            };
            /** @description Bad Gateway */
            502: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "BILLING_UNAVAILABLE",
                     *         "message": "Payment provider is temporarily unavailable."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["BillingErrorResponse"];
                };
            };
            /** @description Service Unavailable */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "BILLING_WEBHOOK_UNAVAILABLE",
                     *         "message": "Billing webhook is not configured."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["BillingErrorResponse"];
                };
            };
        };
    };
    create_setup_api_v1_billing_setup_sessions_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["BillingSetupForm"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["BillingSetupResponse"];
                };
            };
            /** @description Bad Request */
            400: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "BILLING_WEBHOOK_INVALID",
                     *         "message": "Invalid billing webhook."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["BillingErrorResponse"];
                };
            };
            /** @description Unauthorized */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"];
                };
            };
            /** @description Forbidden */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"];
                };
            };
            /** @description Not Found */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["BillingErrorResponse"];
                };
            };
            /** @description Conflict */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "BILLING_CHECKOUT_CONFLICT",
                     *         "message": "An existing subscription or another checkout requires attention."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["BillingErrorResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
            /** @description Unexpected server error */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["InternalErrorResponse"];
                };
            };
            /** @description Bad Gateway */
            502: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "BILLING_UNAVAILABLE",
                     *         "message": "Payment provider is temporarily unavailable."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["BillingErrorResponse"];
                };
            };
            /** @description Service Unavailable */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "BILLING_WEBHOOK_UNAVAILABLE",
                     *         "message": "Billing webhook is not configured."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["BillingErrorResponse"];
                };
            };
        };
    };
    setup_status_api_v1_billing_setup_sessions__session_id__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                session_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["BillingSetupStatusResponse"];
                };
            };
            /** @description Bad Request */
            400: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "BILLING_WEBHOOK_INVALID",
                     *         "message": "Invalid billing webhook."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["BillingErrorResponse"];
                };
            };
            /** @description Unauthorized */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"];
                };
            };
            /** @description Forbidden */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"];
                };
            };
            /** @description Not Found */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["BillingErrorResponse"];
                };
            };
            /** @description Conflict */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "BILLING_CHECKOUT_CONFLICT",
                     *         "message": "An existing subscription or another checkout requires attention."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["BillingErrorResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
            /** @description Unexpected server error */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["InternalErrorResponse"];
                };
            };
            /** @description Bad Gateway */
            502: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "BILLING_UNAVAILABLE",
                     *         "message": "Payment provider is temporarily unavailable."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["BillingErrorResponse"];
                };
            };
            /** @description Service Unavailable */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "BILLING_WEBHOOK_UNAVAILABLE",
                     *         "message": "Billing webhook is not configured."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["BillingErrorResponse"];
                };
            };
        };
    };
    subscription_api_v1_billing_subscription_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["BillingSubscriptionResponse"];
                };
            };
            /** @description Bad Request */
            400: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "BILLING_WEBHOOK_INVALID",
                     *         "message": "Invalid billing webhook."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["BillingErrorResponse"];
                };
            };
            /** @description Unauthorized */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"];
                };
            };
            /** @description Forbidden */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"];
                };
            };
            /** @description Not Found */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["BillingErrorResponse"];
                };
            };
            /** @description Conflict */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "BILLING_CHECKOUT_CONFLICT",
                     *         "message": "An existing subscription or another checkout requires attention."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["BillingErrorResponse"];
                };
            };
            /** @description Unexpected server error */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["InternalErrorResponse"];
                };
            };
            /** @description Bad Gateway */
            502: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "BILLING_UNAVAILABLE",
                     *         "message": "Payment provider is temporarily unavailable."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["BillingErrorResponse"];
                };
            };
            /** @description Service Unavailable */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "BILLING_WEBHOOK_UNAVAILABLE",
                     *         "message": "Billing webhook is not configured."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["BillingErrorResponse"];
                };
            };
        };
    };
    change_subscription_api_v1_billing_subscription_change_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["BillingChangeForm"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["BillingSubscriptionResponse"];
                };
            };
            /** @description Bad Request */
            400: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "BILLING_WEBHOOK_INVALID",
                     *         "message": "Invalid billing webhook."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["BillingErrorResponse"];
                };
            };
            /** @description Unauthorized */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"];
                };
            };
            /** @description Forbidden */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"];
                };
            };
            /** @description Not Found */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["BillingErrorResponse"];
                };
            };
            /** @description Conflict */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "BILLING_CHECKOUT_CONFLICT",
                     *         "message": "An existing subscription or another checkout requires attention."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["BillingErrorResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
            /** @description Unexpected server error */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["InternalErrorResponse"];
                };
            };
            /** @description Bad Gateway */
            502: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "BILLING_UNAVAILABLE",
                     *         "message": "Payment provider is temporarily unavailable."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["BillingErrorResponse"];
                };
            };
            /** @description Service Unavailable */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "BILLING_WEBHOOK_UNAVAILABLE",
                     *         "message": "Billing webhook is not configured."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["BillingErrorResponse"];
                };
            };
        };
    };
    billing_webhook_api_v1_billing_webhook_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: string;
                    };
                };
            };
            /** @description Bad Request */
            400: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "BILLING_WEBHOOK_INVALID",
                     *         "message": "Invalid billing webhook."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["BillingErrorResponse"];
                };
            };
            /** @description Not Found */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "BILLING_NOT_FOUND",
                     *         "message": "Billing resource not found."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["BillingErrorResponse"];
                };
            };
            /** @description Conflict */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "BILLING_CHECKOUT_CONFLICT",
                     *         "message": "An existing subscription or another checkout requires attention."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["BillingErrorResponse"];
                };
            };
            /** @description Unexpected server error */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["InternalErrorResponse"];
                };
            };
            /** @description Bad Gateway */
            502: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "BILLING_UNAVAILABLE",
                     *         "message": "Payment provider is temporarily unavailable."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["BillingErrorResponse"];
                };
            };
            /** @description Service Unavailable */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "BILLING_WEBHOOK_UNAVAILABLE",
                     *         "message": "Billing webhook is not configured."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["BillingErrorResponse"];
                };
            };
        };
    };
    list_boards_api_v1_boards_get: {
        parameters: {
            query?: {
                limit?: number;
                cursor?: string | null;
                q?: string;
                interest_id?: string | null;
                mine?: boolean;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["BoardPageResponse"];
                };
            };
            /** @description Unauthorized */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"];
                };
            };
            /** @description Forbidden */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"];
                };
            };
            /** @description Not Found */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "USER_NOT_FOUND",
                     *         "message": "User not found."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["AuthErrorResponse"];
                };
            };
            /** @description Unprocessable Content */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "BOARD_INVALID_CURSOR",
                     *         "message": "Invalid board cursor. Reload the list."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["BoardErrorResponse"];
                };
            };
            /** @description Unexpected server error */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["InternalErrorResponse"];
                };
            };
        };
    };
    create_board_api_v1_boards_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["BoardCreateForm"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["BoardSummary"];
                };
            };
            /** @description Unauthorized */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"];
                };
            };
            /** @description Forbidden */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"];
                };
            };
            /** @description Not Found */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "USER_NOT_FOUND",
                     *         "message": "User not found."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["AuthErrorResponse"];
                };
            };
            /** @description Conflict */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "BOARD_SLUG_TAKEN",
                     *         "message": "Board slug already exists."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["BoardErrorResponse"];
                };
            };
            /** @description Unprocessable Content */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "BOARD_INVALID_INTEREST",
                     *         "message": "Select active official interests."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["BoardErrorResponse"];
                };
            };
            /** @description Unexpected server error */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["InternalErrorResponse"];
                };
            };
            /** @description Service Unavailable */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "BOARD_UNAVAILABLE",
                     *         "message": "Unable to complete the board operation."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["BoardErrorResponse"];
                };
            };
        };
    };
    home_by_slug_api_v1_boards_by_slug__slug__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                slug: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["BoardHomeResponse"];
                };
            };
            /** @description Unauthorized */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"];
                };
            };
            /** @description Forbidden */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"];
                };
            };
            /** @description Not Found */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["BoardErrorResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
            /** @description Unexpected server error */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["InternalErrorResponse"];
                };
            };
            /** @description Service Unavailable */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "BOARD_UNAVAILABLE",
                     *         "message": "Unable to complete the board operation."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["BoardErrorResponse"];
                };
            };
        };
    };
    board_home_api_v1_boards__board_id__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                board_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["BoardHomeResponse"];
                };
            };
            /** @description Unauthorized */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"];
                };
            };
            /** @description Forbidden */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"];
                };
            };
            /** @description Not Found */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["BoardErrorResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
            /** @description Unexpected server error */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["InternalErrorResponse"];
                };
            };
            /** @description Service Unavailable */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "BOARD_UNAVAILABLE",
                     *         "message": "Unable to complete the board operation."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["BoardErrorResponse"];
                };
            };
        };
    };
    delete_empty_board_api_v1_boards__board_id__delete: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                board_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["BoardDeleteForm"];
            };
        };
        responses: {
            /** @description Successful Response */
            204: {
                headers: {
                    [name: string]: unknown;
                };
                content?: never;
            };
            /** @description Unauthorized */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"];
                };
            };
            /** @description Forbidden */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"]
                        | components["schemas"]["BoardErrorResponse"];
                };
            };
            /** @description Not Found */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["BoardErrorResponse"];
                };
            };
            /** @description Conflict */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "BOARD_REVISION_CONFLICT",
                     *         "message": "Board revision conflict. Reload the latest board information."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["BoardErrorResponse"];
                };
            };
            /** @description Unprocessable Content */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "BOARD_DELETE_CONFIRMATION",
                     *         "message": "Enter the exact board slug to confirm deletion."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["BoardErrorResponse"];
                };
            };
            /** @description Unexpected server error */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["InternalErrorResponse"];
                };
            };
            /** @description Service Unavailable */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "BOARD_UNAVAILABLE",
                     *         "message": "Unable to complete the board operation."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["BoardErrorResponse"];
                };
            };
        };
    };
    update_board_api_v1_boards__board_id__patch: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                board_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["BoardSettingsPatchForm"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["BoardUpdateResponse"];
                };
            };
            /** @description Unauthorized */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"];
                };
            };
            /** @description Forbidden */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"]
                        | components["schemas"]["BoardErrorResponse"];
                };
            };
            /** @description Not Found */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["BoardErrorResponse"];
                };
            };
            /** @description Conflict */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "BOARD_REVISION_CONFLICT",
                     *         "message": "Board revision conflict. Reload the latest board information."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["BoardErrorResponse"];
                };
            };
            /** @description Unprocessable Content */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "BOARD_INVALID_INTEREST",
                     *         "message": "Select active official interests."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["BoardErrorResponse"];
                };
            };
            /** @description Unexpected server error */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["InternalErrorResponse"];
                };
            };
            /** @description Service Unavailable */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "BOARD_UNAVAILABLE",
                     *         "message": "Unable to complete the board operation."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["BoardErrorResponse"];
                };
            };
        };
    };
    create_canvas_api_v1_boards__board_id__canvases_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                board_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["CanvasCreateForm"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["CanvasResponse"];
                };
            };
            /** @description Unauthorized */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"];
                };
            };
            /** @description Forbidden */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"]
                        | components["schemas"]["CanvasErrorResponse"];
                };
            };
            /** @description Not Found */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["CanvasErrorResponse"];
                };
            };
            /** @description Unprocessable Content */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "CANVAS_INVALID_SHELF",
                     *         "message": "Select a manual shelf in the same board."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["CanvasErrorResponse"];
                };
            };
            /** @description Unexpected server error */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["InternalErrorResponse"];
                };
            };
            /** @description Service Unavailable */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "CANVAS_UNAVAILABLE",
                     *         "message": "Unable to complete the canvas operation."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["CanvasErrorResponse"];
                };
            };
        };
    };
    grades_api_v1_boards__board_id__grades_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                board_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["BoardGradesResponse"];
                };
            };
            /** @description Unauthorized */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"];
                };
            };
            /** @description Forbidden */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"];
                };
            };
            /** @description Not Found */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["BoardErrorResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
            /** @description Unexpected server error */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["InternalErrorResponse"];
                };
            };
            /** @description Service Unavailable */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "BOARD_UNAVAILABLE",
                     *         "message": "Unable to complete the board operation."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["BoardErrorResponse"];
                };
            };
        };
    };
    create_grade_api_v1_boards__board_id__grades_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                board_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["BoardGradeCreateForm"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["BoardGradeResponse"];
                };
            };
            /** @description Unauthorized */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"];
                };
            };
            /** @description Forbidden */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"]
                        | components["schemas"]["BoardErrorResponse"];
                };
            };
            /** @description Not Found */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["BoardErrorResponse"];
                };
            };
            /** @description Conflict */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "BOARD_REVISION_CONFLICT",
                     *         "message": "Board revision conflict. Reload the latest board information."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["BoardErrorResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
            /** @description Unexpected server error */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["InternalErrorResponse"];
                };
            };
            /** @description Service Unavailable */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "BOARD_UNAVAILABLE",
                     *         "message": "Unable to complete the board operation."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["BoardErrorResponse"];
                };
            };
        };
    };
    reorder_grades_api_v1_boards__board_id__grades_order_patch: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                board_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["BoardGradeOrderForm"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["BoardGradesResponse"];
                };
            };
            /** @description Unauthorized */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"];
                };
            };
            /** @description Forbidden */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"]
                        | components["schemas"]["BoardErrorResponse"];
                };
            };
            /** @description Not Found */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["BoardErrorResponse"];
                };
            };
            /** @description Conflict */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "BOARD_REVISION_CONFLICT",
                     *         "message": "Board revision conflict. Reload the latest board information."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["BoardErrorResponse"];
                };
            };
            /** @description Unprocessable Content */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "BOARD_INVALID_GRADE_ORDER",
                     *         "message": "Provide every grade in this board exactly once."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["BoardErrorResponse"];
                };
            };
            /** @description Unexpected server error */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["InternalErrorResponse"];
                };
            };
            /** @description Service Unavailable */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "BOARD_UNAVAILABLE",
                     *         "message": "Unable to complete the board operation."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["BoardErrorResponse"];
                };
            };
        };
    };
    delete_grade_api_v1_boards__board_id__grades__grade_id__delete: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                board_id: string;
                grade_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["BoardGradeDeleteForm"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["BoardGradesResponse"];
                };
            };
            /** @description Unauthorized */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"];
                };
            };
            /** @description Forbidden */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"]
                        | components["schemas"]["BoardErrorResponse"];
                };
            };
            /** @description Not Found */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["BoardErrorResponse"];
                };
            };
            /** @description Conflict */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "BOARD_REVISION_CONFLICT",
                     *         "message": "Board revision conflict. Reload the latest board information."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["BoardErrorResponse"];
                };
            };
            /** @description Unprocessable Content */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "BOARD_INVALID_GRADE",
                     *         "message": "Select a member grade from the same board."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["BoardErrorResponse"];
                };
            };
            /** @description Unexpected server error */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["InternalErrorResponse"];
                };
            };
            /** @description Service Unavailable */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "BOARD_UNAVAILABLE",
                     *         "message": "Unable to complete the board operation."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["BoardErrorResponse"];
                };
            };
        };
    };
    change_grade_api_v1_boards__board_id__grades__grade_id__patch: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                board_id: string;
                grade_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["BoardGradePatchForm"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["BoardGradeResponse"];
                };
            };
            /** @description Unauthorized */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"];
                };
            };
            /** @description Forbidden */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"]
                        | components["schemas"]["BoardErrorResponse"];
                };
            };
            /** @description Not Found */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["BoardErrorResponse"];
                };
            };
            /** @description Conflict */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "BOARD_REVISION_CONFLICT",
                     *         "message": "Board revision conflict. Reload the latest board information."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["BoardErrorResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
            /** @description Unexpected server error */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["InternalErrorResponse"];
                };
            };
            /** @description Service Unavailable */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "BOARD_UNAVAILABLE",
                     *         "message": "Unable to complete the board operation."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["BoardErrorResponse"];
                };
            };
        };
    };
    board_home_api_v1_boards__board_id__home_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                board_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["BoardHomeResponse"];
                };
            };
            /** @description Unauthorized */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"];
                };
            };
            /** @description Forbidden */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"];
                };
            };
            /** @description Not Found */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["BoardErrorResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
            /** @description Unexpected server error */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["InternalErrorResponse"];
                };
            };
            /** @description Service Unavailable */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "BOARD_UNAVAILABLE",
                     *         "message": "Unable to complete the board operation."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["BoardErrorResponse"];
                };
            };
        };
    };
    join_board_api_v1_boards__board_id__join_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                board_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["MembershipSummary"];
                };
            };
            /** @description Unauthorized */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"];
                };
            };
            /** @description Forbidden */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"]
                        | components["schemas"]["BoardErrorResponse"];
                };
            };
            /** @description Not Found */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["BoardErrorResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
            /** @description Unexpected server error */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["InternalErrorResponse"];
                };
            };
            /** @description Service Unavailable */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "BOARD_UNAVAILABLE",
                     *         "message": "Unable to complete the board operation."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["BoardErrorResponse"];
                };
            };
        };
    };
    member_audit_api_v1_boards__board_id__member_audit_get: {
        parameters: {
            query: {
                since: string;
                until: string;
                limit?: number;
                cursor?: string | null;
                target_user_id?: number | null;
            };
            header?: never;
            path: {
                board_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["BoardAuditPageResponse"];
                };
            };
            /** @description Unauthorized */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"];
                };
            };
            /** @description Forbidden */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"]
                        | components["schemas"]["BoardErrorResponse"];
                };
            };
            /** @description Not Found */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["BoardErrorResponse"];
                };
            };
            /** @description Unprocessable Content */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "BOARD_INVALID_CURSOR",
                     *         "message": "Invalid board cursor. Reload the list."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["BoardErrorResponse"];
                };
            };
            /** @description Unexpected server error */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["InternalErrorResponse"];
                };
            };
            /** @description Service Unavailable */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "BOARD_UNAVAILABLE",
                     *         "message": "Unable to complete the board operation."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["BoardErrorResponse"];
                };
            };
        };
    };
    members_api_v1_boards__board_id__members_get: {
        parameters: {
            query?: {
                limit?: number;
                cursor?: string | null;
                q?: string;
                role?: ("owner" | "admin" | "moderator" | "member") | null;
                status?: ("active" | "pending" | "suspended" | "banned") | null;
            };
            header?: never;
            path: {
                board_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["BoardMemberListResponse"];
                };
            };
            /** @description Unauthorized */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"];
                };
            };
            /** @description Forbidden */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"]
                        | components["schemas"]["BoardErrorResponse"];
                };
            };
            /** @description Not Found */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["BoardErrorResponse"];
                };
            };
            /** @description Unprocessable Content */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "BOARD_INVALID_CURSOR",
                     *         "message": "Invalid board cursor. Reload the list."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["BoardErrorResponse"];
                };
            };
            /** @description Unexpected server error */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["InternalErrorResponse"];
                };
            };
            /** @description Service Unavailable */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "BOARD_UNAVAILABLE",
                     *         "message": "Unable to complete the board operation."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["BoardErrorResponse"];
                };
            };
        };
    };
    invite_member_api_v1_boards__board_id__members_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                board_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["BoardMemberInviteForm"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["BoardMemberUpdateResponse"];
                };
            };
            /** @description Unauthorized */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"];
                };
            };
            /** @description Forbidden */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"]
                        | components["schemas"]["BoardErrorResponse"];
                };
            };
            /** @description Not Found */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["BoardErrorResponse"];
                };
            };
            /** @description Conflict */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "BOARD_REVISION_CONFLICT",
                     *         "message": "Board revision conflict. Reload the latest board information."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["BoardErrorResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
            /** @description Unexpected server error */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["InternalErrorResponse"];
                };
            };
            /** @description Service Unavailable */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "BOARD_UNAVAILABLE",
                     *         "message": "Unable to complete the board operation."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["BoardErrorResponse"];
                };
            };
        };
    };
    update_member_api_v1_boards__board_id__members__user_id__patch: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                board_id: string;
                user_id: number;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["BoardMemberPatchForm"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["BoardMemberUpdateResponse"];
                };
            };
            /** @description Unauthorized */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"];
                };
            };
            /** @description Forbidden */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"]
                        | components["schemas"]["BoardErrorResponse"];
                };
            };
            /** @description Not Found */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["BoardErrorResponse"];
                };
            };
            /** @description Conflict */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "BOARD_REVISION_CONFLICT",
                     *         "message": "Board revision conflict. Reload the latest board information."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["BoardErrorResponse"];
                };
            };
            /** @description Unprocessable Content */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "BOARD_INVALID_GRADE",
                     *         "message": "Select a member grade from the same board."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["BoardErrorResponse"];
                };
            };
            /** @description Unexpected server error */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["InternalErrorResponse"];
                };
            };
            /** @description Service Unavailable */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "BOARD_UNAVAILABLE",
                     *         "message": "Unable to complete the board operation."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["BoardErrorResponse"];
                };
            };
        };
    };
    leave_board_api_v1_boards__board_id__membership_delete: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                board_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            204: {
                headers: {
                    [name: string]: unknown;
                };
                content?: never;
            };
            /** @description Unauthorized */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"];
                };
            };
            /** @description Forbidden */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"]
                        | components["schemas"]["BoardErrorResponse"];
                };
            };
            /** @description Not Found */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["BoardErrorResponse"];
                };
            };
            /** @description Conflict */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "BOARD_OWNER_CANNOT_LEAVE",
                     *         "message": "Transfer ownership or delete the board before leaving."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["BoardErrorResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
            /** @description Unexpected server error */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["InternalErrorResponse"];
                };
            };
            /** @description Service Unavailable */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "BOARD_UNAVAILABLE",
                     *         "message": "Unable to complete the board operation."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["BoardErrorResponse"];
                };
            };
        };
    };
    transfer_board_ownership_api_v1_boards__board_id__ownership_transfer_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                board_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["BoardOwnershipTransferForm"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["BoardOwnershipTransferResponse"];
                };
            };
            /** @description Unauthorized */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"];
                };
            };
            /** @description Forbidden */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"]
                        | components["schemas"]["BoardErrorResponse"];
                };
            };
            /** @description Not Found */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["BoardErrorResponse"];
                };
            };
            /** @description Conflict */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "BOARD_REVISION_CONFLICT",
                     *         "message": "Board revision conflict. Reload the latest board information."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["BoardErrorResponse"];
                };
            };
            /** @description Unprocessable Content */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "BOARD_INVALID_OWNERSHIP_TARGET",
                     *         "message": "Select another active member of this board with an active account."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["BoardErrorResponse"];
                };
            };
            /** @description Unexpected server error */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["InternalErrorResponse"];
                };
            };
            /** @description Service Unavailable */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "BOARD_UNAVAILABLE",
                     *         "message": "Unable to complete the board operation."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["BoardErrorResponse"];
                };
            };
        };
    };
    board_policies_api_v1_boards__board_id__policies_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                board_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["BoardPoliciesResponse"];
                };
            };
            /** @description Unauthorized */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"];
                };
            };
            /** @description Forbidden */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"]
                        | components["schemas"]["BoardErrorResponse"];
                };
            };
            /** @description Not Found */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["BoardErrorResponse"]
                        | components["schemas"]["ShelfErrorResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
            /** @description Unexpected server error */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["InternalErrorResponse"];
                };
            };
            /** @description Service Unavailable */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "BOARD_UNAVAILABLE",
                     *         "message": "Unable to complete the board operation."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["BoardErrorResponse"];
                };
            };
        };
    };
    set_board_policies_api_v1_boards__board_id__policies_put: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                board_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["BoardPoliciesForm"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["BoardPoliciesResponse"];
                };
            };
            /** @description Unauthorized */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"];
                };
            };
            /** @description Forbidden */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"]
                        | components["schemas"]["BoardErrorResponse"];
                };
            };
            /** @description Not Found */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["BoardErrorResponse"]
                        | components["schemas"]["ShelfErrorResponse"];
                };
            };
            /** @description Conflict */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "BOARD_REVISION_CONFLICT",
                     *         "message": "Board revision conflict. Reload the latest board information."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["BoardErrorResponse"];
                };
            };
            /** @description Unprocessable Content */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "BOARD_INVALID_GRADE",
                     *         "message": "Select a member grade from the same board."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["BoardErrorResponse"];
                };
            };
            /** @description Unexpected server error */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["InternalErrorResponse"];
                };
            };
            /** @description Service Unavailable */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "BOARD_UNAVAILABLE",
                     *         "message": "Unable to complete the board operation."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["BoardErrorResponse"];
                };
            };
        };
    };
    list_shelves_api_v1_boards__board_id__shelves_get: {
        parameters: {
            query?: {
                manage?: boolean;
            };
            header?: never;
            path: {
                board_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ShelvesResponse"];
                };
            };
            /** @description Unauthorized */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"];
                };
            };
            /** @description Forbidden */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"]
                        | components["schemas"]["BoardErrorResponse"];
                };
            };
            /** @description Not Found */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["BoardErrorResponse"]
                        | components["schemas"]["ShelfErrorResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
            /** @description Unexpected server error */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["InternalErrorResponse"];
                };
            };
            /** @description Service Unavailable */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "BOARD_UNAVAILABLE",
                     *         "message": "Unable to complete the board operation."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["BoardErrorResponse"];
                };
            };
        };
    };
    create_shelf_api_v1_boards__board_id__shelves_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                board_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["ShelfCreateForm"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ShelfResponse"];
                };
            };
            /** @description Unauthorized */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"];
                };
            };
            /** @description Forbidden */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"]
                        | components["schemas"]["BoardErrorResponse"];
                };
            };
            /** @description Not Found */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["BoardErrorResponse"]
                        | components["schemas"]["ShelfErrorResponse"];
                };
            };
            /** @description Conflict */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["BoardErrorResponse"]
                        | components["schemas"]["ShelfErrorResponse"];
                };
            };
            /** @description Unprocessable Content */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "BOARD_INVALID_GRADE",
                     *         "message": "Select a member grade from the same board."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["BoardErrorResponse"];
                };
            };
            /** @description Unexpected server error */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["InternalErrorResponse"];
                };
            };
            /** @description Service Unavailable */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "BOARD_UNAVAILABLE",
                     *         "message": "Unable to complete the board operation."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["BoardErrorResponse"];
                };
            };
        };
    };
    reorder_shelves_api_v1_boards__board_id__shelves_order_patch: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                board_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["ShelfOrderForm"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ShelvesResponse"];
                };
            };
            /** @description Unauthorized */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"];
                };
            };
            /** @description Forbidden */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"]
                        | components["schemas"]["BoardErrorResponse"];
                };
            };
            /** @description Not Found */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["BoardErrorResponse"]
                        | components["schemas"]["ShelfErrorResponse"];
                };
            };
            /** @description Conflict */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "BOARD_REVISION_CONFLICT",
                     *         "message": "Board revision conflict. Reload the latest board information."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["BoardErrorResponse"];
                };
            };
            /** @description Unprocessable Content */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["BoardErrorResponse"]
                        | components["schemas"]["ShelfErrorResponse"];
                };
            };
            /** @description Unexpected server error */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["InternalErrorResponse"];
                };
            };
            /** @description Service Unavailable */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "BOARD_UNAVAILABLE",
                     *         "message": "Unable to complete the board operation."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["BoardErrorResponse"];
                };
            };
        };
    };
    get_canvas_api_v1_canvases__canvas_id__get: {
        parameters: {
            query?: {
                view?: "draft";
            };
            header?: never;
            path: {
                canvas_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["CanvasResponse"];
                };
            };
            /** @description Unauthorized */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"];
                };
            };
            /** @description Forbidden */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"];
                };
            };
            /** @description Not Found */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["CanvasErrorResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
            /** @description Unexpected server error */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["InternalErrorResponse"];
                };
            };
            /** @description Service Unavailable */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "CANVAS_UNAVAILABLE",
                     *         "message": "Unable to complete the canvas operation."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["CanvasErrorResponse"];
                };
            };
        };
    };
    trash_canvas_api_v1_canvases__canvas_id__delete: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                canvas_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["CanvasRevisionForm"];
            };
        };
        responses: {
            /** @description Successful Response */
            204: {
                headers: {
                    [name: string]: unknown;
                };
                content?: never;
            };
            /** @description Unauthorized */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"];
                };
            };
            /** @description Forbidden */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"]
                        | components["schemas"]["CanvasErrorResponse"];
                };
            };
            /** @description Not Found */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["CanvasErrorResponse"];
                };
            };
            /** @description Conflict */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "CANVAS_REVISION_CONFLICT",
                     *         "message": "Canvas metadata revision conflict. Reload the latest canvas."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["CanvasErrorResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
            /** @description Unexpected server error */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["InternalErrorResponse"];
                };
            };
            /** @description Service Unavailable */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "CANVAS_UNAVAILABLE",
                     *         "message": "Unable to complete the canvas operation."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["CanvasErrorResponse"];
                };
            };
        };
    };
    change_canvas_api_v1_canvases__canvas_id__patch: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                canvas_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["CanvasPatchForm"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["CanvasResponse"];
                };
            };
            /** @description Unauthorized */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"];
                };
            };
            /** @description Forbidden */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"]
                        | components["schemas"]["CanvasErrorResponse"];
                };
            };
            /** @description Not Found */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["CanvasErrorResponse"];
                };
            };
            /** @description Conflict */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "CANVAS_REVISION_CONFLICT",
                     *         "message": "Canvas metadata revision conflict. Reload the latest canvas."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["CanvasErrorResponse"];
                };
            };
            /** @description Unprocessable Content */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "CANVAS_INVALID_SHELF",
                     *         "message": "Select a manual shelf in the same board."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["CanvasErrorResponse"];
                };
            };
            /** @description Unexpected server error */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["InternalErrorResponse"];
                };
            };
            /** @description Service Unavailable */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "CANVAS_UNAVAILABLE",
                     *         "message": "Unable to complete the canvas operation."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["CanvasErrorResponse"];
                };
            };
        };
    };
    upload_asset_api_v1_canvases__canvas_id__assets_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                canvas_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "multipart/form-data": components["schemas"]["Body_upload_asset_api_v1_canvases__canvas_id__assets_post"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AssetResponse"];
                };
            };
            /** @description Unauthorized */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"];
                };
            };
            /** @description Forbidden */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"]
                        | components["schemas"]["CanvasErrorResponse"];
                };
            };
            /** @description Not Found */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["CanvasErrorResponse"];
                };
            };
            /** @description Conflict */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["CanvasErrorResponse"]
                        | components["schemas"]["AssetErrorResponse"];
                };
            };
            /** @description Content Too Large */
            413: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "ASSET_TOO_LARGE",
                     *         "message": "Image upload or normalized output exceeds 8 MiB."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["AssetErrorResponse"];
                };
            };
            /** @description Unprocessable Content */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "ASSET_INVALID_IMAGE",
                     *         "message": "Upload a supported image within the pixel and frame limits."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["AssetErrorResponse"];
                };
            };
            /** @description Unexpected server error */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["InternalErrorResponse"];
                };
            };
            /** @description Service Unavailable */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["CanvasErrorResponse"]
                        | components["schemas"]["AssetErrorResponse"];
                };
            };
        };
    };
    read_asset_api_v1_canvases__canvas_id__assets__asset_id__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                canvas_id: string;
                asset_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Private normalized image. */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "image/webp": string;
                };
            };
            /** @description Unauthorized */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"];
                };
            };
            /** @description Forbidden */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"]
                        | components["schemas"]["CanvasErrorResponse"];
                };
            };
            /** @description Not Found */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["CanvasErrorResponse"]
                        | components["schemas"]["AssetErrorResponse"];
                };
            };
            /** @description Conflict */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "CANVAS_INVALID_STATE",
                     *         "message": "Restore the canvas before editing it."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["CanvasErrorResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
            /** @description Unexpected server error */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["InternalErrorResponse"];
                };
            };
            /** @description Service Unavailable */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["CanvasErrorResponse"]
                        | components["schemas"]["AssetErrorResponse"];
                };
            };
        };
    };
    delete_asset_api_v1_canvases__canvas_id__assets__asset_id__delete: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                canvas_id: string;
                asset_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            204: {
                headers: {
                    [name: string]: unknown;
                };
                content?: never;
            };
            /** @description Unauthorized */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"];
                };
            };
            /** @description Forbidden */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"]
                        | components["schemas"]["CanvasErrorResponse"];
                };
            };
            /** @description Not Found */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["CanvasErrorResponse"]
                        | components["schemas"]["AssetErrorResponse"];
                };
            };
            /** @description Conflict */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["CanvasErrorResponse"]
                        | components["schemas"]["AssetErrorResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
            /** @description Unexpected server error */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["InternalErrorResponse"];
                };
            };
            /** @description Service Unavailable */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["CanvasErrorResponse"]
                        | components["schemas"]["AssetErrorResponse"];
                };
            };
        };
    };
    get_canvas_document_api_v1_canvases__canvas_id__document_get: {
        parameters: {
            query?: {
                view?: "draft";
            };
            header?: never;
            path: {
                canvas_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["CanvasDocumentResponse"];
                };
            };
            /** @description Unauthorized */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"];
                };
            };
            /** @description Forbidden */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"];
                };
            };
            /** @description Not Found */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["CanvasErrorResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
            /** @description Unexpected server error */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["InternalErrorResponse"];
                };
            };
            /** @description Service Unavailable */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "CANVAS_UNAVAILABLE",
                     *         "message": "Unable to complete the canvas operation."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["CanvasErrorResponse"];
                };
            };
        };
    };
    restore_canvas_api_v1_canvases__canvas_id__restore_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                canvas_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["CanvasRevisionForm"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["CanvasResponse"];
                };
            };
            /** @description Unauthorized */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"];
                };
            };
            /** @description Forbidden */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"]
                        | components["schemas"]["CanvasErrorResponse"];
                };
            };
            /** @description Not Found */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["CanvasErrorResponse"];
                };
            };
            /** @description Conflict */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "CANVAS_REVISION_CONFLICT",
                     *         "message": "Canvas metadata revision conflict. Reload the latest canvas."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["CanvasErrorResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
            /** @description Unexpected server error */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["InternalErrorResponse"];
                };
            };
            /** @description Service Unavailable */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "CANVAS_UNAVAILABLE",
                     *         "message": "Unable to complete the canvas operation."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["CanvasErrorResponse"];
                };
            };
        };
    };
    stream_events_api_v1_events_stream_get: {
        parameters: {
            query?: never;
            header?: {
                /** @description Accepted for diagnostics only; events are not replayed. */
                "last-event-id"?: string | null;
            };
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description SSE frames; each data field contains a RealtimeStreamEvent JSON value. No replay is provided; re-fetch affected resources after reconnecting. */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "text/event-stream": string;
                };
            };
            /** @description Unauthorized */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"];
                };
            };
            /** @description Forbidden */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"];
                };
            };
            /** @description Not Found */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "USER_NOT_FOUND",
                     *         "message": "User not found."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["AuthErrorResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
            /** @description Unexpected server error */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["InternalErrorResponse"];
                };
            };
        };
    };
    list_notifications_api_v1_inbox_get: {
        parameters: {
            query?: {
                page?: number;
                page_size?: number;
                unread_only?: boolean;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["InboxPage"];
                };
            };
            /** @description Unauthorized */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"];
                };
            };
            /** @description Forbidden */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"];
                };
            };
            /** @description Not Found */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "USER_NOT_FOUND",
                     *         "message": "User not found."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["AuthErrorResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
            /** @description Unexpected server error */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["InternalErrorResponse"];
                };
            };
        };
    };
    read_all_api_v1_inbox_read_all_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["InboxReadAllForm"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["InboxSummary"];
                };
            };
            /** @description Unauthorized */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"];
                };
            };
            /** @description Forbidden */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"];
                };
            };
            /** @description Not Found */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "USER_NOT_FOUND",
                     *         "message": "User not found."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["AuthErrorResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
            /** @description Unexpected server error */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["InternalErrorResponse"];
                };
            };
        };
    };
    read_selected_api_v1_inbox_read_selected_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["InboxSelectionForm"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["InboxSummary"];
                };
            };
            /** @description Unauthorized */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"];
                };
            };
            /** @description Forbidden */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"];
                };
            };
            /** @description Not Found */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "USER_NOT_FOUND",
                     *         "message": "User not found."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["AuthErrorResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
            /** @description Unexpected server error */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["InternalErrorResponse"];
                };
            };
        };
    };
    delete_selected_api_v1_inbox_selected_delete: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["InboxSelectionForm"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["InboxSummary"];
                };
            };
            /** @description Unauthorized */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"];
                };
            };
            /** @description Forbidden */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"];
                };
            };
            /** @description Not Found */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "USER_NOT_FOUND",
                     *         "message": "User not found."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["AuthErrorResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
            /** @description Unexpected server error */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["InternalErrorResponse"];
                };
            };
        };
    };
    summary_api_v1_inbox_summary_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["InboxSummary"];
                };
            };
            /** @description Unauthorized */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"];
                };
            };
            /** @description Forbidden */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"];
                };
            };
            /** @description Not Found */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "USER_NOT_FOUND",
                     *         "message": "User not found."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["AuthErrorResponse"];
                };
            };
            /** @description Unexpected server error */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["InternalErrorResponse"];
                };
            };
        };
    };
    read_api_v1_inbox__notification_id__read_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                notification_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["InboxItem"];
                };
            };
            /** @description Unauthorized */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"];
                };
            };
            /** @description Forbidden */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"];
                };
            };
            /** @description Not Found */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["InboxErrorResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
            /** @description Unexpected server error */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["InternalErrorResponse"];
                };
            };
        };
    };
    list_own_api_v1_inquiries_get: {
        parameters: {
            query?: {
                page?: number;
                page_size?: number;
                status?: components["schemas"]["InquiryStatus"] | null;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["InquiryPage"];
                };
            };
            /** @description Unauthorized */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"];
                };
            };
            /** @description Forbidden */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"];
                };
            };
            /** @description Not Found */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "USER_NOT_FOUND",
                     *         "message": "User not found."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["AuthErrorResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
            /** @description Unexpected server error */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["InternalErrorResponse"];
                };
            };
        };
    };
    create_api_v1_inquiries_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["InquiryCreate"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["InquiryDetail"];
                };
            };
            /** @description Unauthorized */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"];
                };
            };
            /** @description Forbidden */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"];
                };
            };
            /** @description Not Found */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["InquiryErrorResponse"];
                };
            };
            /** @description Conflict */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "INQUIRY_CLOSED",
                     *         "message": "This inquiry is closed."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["InquiryErrorResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
            /** @description Unexpected server error */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["InternalErrorResponse"];
                };
            };
        };
    };
    list_all_api_v1_inquiries_admin_get: {
        parameters: {
            query?: {
                page?: number;
                page_size?: number;
                status?: components["schemas"]["InquiryStatus"] | null;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["InquiryPage"];
                };
            };
            /** @description Unauthorized */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"];
                };
            };
            /** @description Forbidden */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"];
                };
            };
            /** @description Not Found */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "USER_NOT_FOUND",
                     *         "message": "User not found."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["AuthErrorResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
            /** @description Unexpected server error */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["InternalErrorResponse"];
                };
            };
        };
    };
    detail_api_v1_inquiries__inquiry_id__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                inquiry_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["InquiryDetail"];
                };
            };
            /** @description Unauthorized */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"];
                };
            };
            /** @description Forbidden */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"];
                };
            };
            /** @description Not Found */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["InquiryErrorResponse"];
                };
            };
            /** @description Conflict */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "INQUIRY_CLOSED",
                     *         "message": "This inquiry is closed."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["InquiryErrorResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
            /** @description Unexpected server error */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["InternalErrorResponse"];
                };
            };
        };
    };
    reply_api_v1_inquiries__inquiry_id__messages_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                inquiry_id: number;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["InquiryReply"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["InquiryDetail"];
                };
            };
            /** @description Unauthorized */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"];
                };
            };
            /** @description Forbidden */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"];
                };
            };
            /** @description Not Found */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["InquiryErrorResponse"];
                };
            };
            /** @description Conflict */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "INQUIRY_CLOSED",
                     *         "message": "This inquiry is closed."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["InquiryErrorResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
            /** @description Unexpected server error */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["InternalErrorResponse"];
                };
            };
        };
    };
    change_status_api_v1_inquiries__inquiry_id__status_patch: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                inquiry_id: number;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["InquiryStatusForm"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["InquiryDetail"];
                };
            };
            /** @description Unauthorized */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"];
                };
            };
            /** @description Forbidden */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"];
                };
            };
            /** @description Not Found */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["InquiryErrorResponse"];
                };
            };
            /** @description Conflict */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "INQUIRY_CLOSED",
                     *         "message": "This inquiry is closed."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["InquiryErrorResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
            /** @description Unexpected server error */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["InternalErrorResponse"];
                };
            };
        };
    };
    catalog_api_v1_interests_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["InterestCatalogResponse"];
                };
            };
            /** @description Unexpected server error */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["InternalErrorResponse"];
                };
            };
        };
    };
    list_admin_api_v1_interests_admin_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["InterestAdminResponse"][];
                };
            };
            /** @description Unauthorized */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"];
                };
            };
            /** @description Forbidden */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"];
                };
            };
            /** @description Not Found */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "USER_NOT_FOUND",
                     *         "message": "User not found."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["AuthErrorResponse"];
                };
            };
            /** @description Unexpected server error */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["InternalErrorResponse"];
                };
            };
        };
    };
    create_api_v1_interests_admin_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["InterestCreateForm"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["InterestAdminResponse"];
                };
            };
            /** @description Unauthorized */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"];
                };
            };
            /** @description Forbidden */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"];
                };
            };
            /** @description Not Found */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "USER_NOT_FOUND",
                     *         "message": "User not found."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["AuthErrorResponse"];
                };
            };
            /** @description Conflict */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "INTEREST_ALREADY_EXISTS",
                     *         "message": "An interest identifier or alias is already in use."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["AuthErrorResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
            /** @description Unexpected server error */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["InternalErrorResponse"];
                };
            };
        };
    };
    update_api_v1_interests_admin__interest_id__patch: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                interest_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["InterestUpdateForm"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["InterestAdminResponse"];
                };
            };
            /** @description Unauthorized */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"];
                };
            };
            /** @description Forbidden */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"];
                };
            };
            /** @description Not Found */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AuthErrorResponse"];
                };
            };
            /** @description Conflict */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "INTEREST_ALREADY_EXISTS",
                     *         "message": "An interest identifier or alias is already in use."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["AuthErrorResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
            /** @description Unexpected server error */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["InternalErrorResponse"];
                };
            };
        };
    };
    get_shelf_api_v1_shelves__shelf_id__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                shelf_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ShelfResponse"];
                };
            };
            /** @description Unauthorized */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"];
                };
            };
            /** @description Forbidden */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"]
                        | components["schemas"]["BoardErrorResponse"];
                };
            };
            /** @description Not Found */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["BoardErrorResponse"]
                        | components["schemas"]["ShelfErrorResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
            /** @description Unexpected server error */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["InternalErrorResponse"];
                };
            };
            /** @description Service Unavailable */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "BOARD_UNAVAILABLE",
                     *         "message": "Unable to complete the board operation."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["BoardErrorResponse"];
                };
            };
        };
    };
    delete_shelf_api_v1_shelves__shelf_id__delete: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                shelf_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["PolicyChangeForm"];
            };
        };
        responses: {
            /** @description Successful Response */
            204: {
                headers: {
                    [name: string]: unknown;
                };
                content?: never;
            };
            /** @description Unauthorized */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"];
                };
            };
            /** @description Forbidden */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"]
                        | components["schemas"]["BoardErrorResponse"];
                };
            };
            /** @description Not Found */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["BoardErrorResponse"]
                        | components["schemas"]["ShelfErrorResponse"];
                };
            };
            /** @description Conflict */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["BoardErrorResponse"]
                        | components["schemas"]["ShelfErrorResponse"];
                };
            };
            /** @description Unprocessable Content */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "BOARD_INVALID_GRADE",
                     *         "message": "Select a member grade from the same board."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["BoardErrorResponse"];
                };
            };
            /** @description Unexpected server error */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["InternalErrorResponse"];
                };
            };
            /** @description Service Unavailable */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "BOARD_UNAVAILABLE",
                     *         "message": "Unable to complete the board operation."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["BoardErrorResponse"];
                };
            };
        };
    };
    change_shelf_api_v1_shelves__shelf_id__patch: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                shelf_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["ShelfPatchForm"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ShelfResponse"];
                };
            };
            /** @description Unauthorized */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"];
                };
            };
            /** @description Forbidden */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"]
                        | components["schemas"]["BoardErrorResponse"];
                };
            };
            /** @description Not Found */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["BoardErrorResponse"]
                        | components["schemas"]["ShelfErrorResponse"];
                };
            };
            /** @description Conflict */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["BoardErrorResponse"]
                        | components["schemas"]["ShelfErrorResponse"];
                };
            };
            /** @description Unprocessable Content */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "BOARD_INVALID_GRADE",
                     *         "message": "Select a member grade from the same board."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["BoardErrorResponse"];
                };
            };
            /** @description Unexpected server error */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["InternalErrorResponse"];
                };
            };
            /** @description Service Unavailable */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "BOARD_UNAVAILABLE",
                     *         "message": "Unable to complete the board operation."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["BoardErrorResponse"];
                };
            };
        };
    };
    shelf_policies_api_v1_shelves__shelf_id__policies_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                shelf_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ShelfPoliciesResponse"];
                };
            };
            /** @description Unauthorized */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"];
                };
            };
            /** @description Forbidden */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"]
                        | components["schemas"]["BoardErrorResponse"];
                };
            };
            /** @description Not Found */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["BoardErrorResponse"]
                        | components["schemas"]["ShelfErrorResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
            /** @description Unexpected server error */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["InternalErrorResponse"];
                };
            };
            /** @description Service Unavailable */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "BOARD_UNAVAILABLE",
                     *         "message": "Unable to complete the board operation."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["BoardErrorResponse"];
                };
            };
        };
    };
    set_shelf_policies_api_v1_shelves__shelf_id__policies_put: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                shelf_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["ShelfPoliciesForm"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ShelfPoliciesResponse"];
                };
            };
            /** @description Unauthorized */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"];
                };
            };
            /** @description Forbidden */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["APIKeyErrorResponse"]
                        | components["schemas"]["BoardErrorResponse"];
                };
            };
            /** @description Not Found */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["AuthErrorResponse"]
                        | components["schemas"]["BoardErrorResponse"]
                        | components["schemas"]["ShelfErrorResponse"];
                };
            };
            /** @description Conflict */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "BOARD_REVISION_CONFLICT",
                     *         "message": "Board revision conflict. Reload the latest board information."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["BoardErrorResponse"];
                };
            };
            /** @description Unprocessable Content */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json":
                        | components["schemas"]["BoardErrorResponse"]
                        | components["schemas"]["ShelfErrorResponse"];
                };
            };
            /** @description Unexpected server error */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["InternalErrorResponse"];
                };
            };
            /** @description Service Unavailable */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    /**
                     * @example {
                     *       "detail": {
                     *         "error": "BOARD_UNAVAILABLE",
                     *         "message": "Unable to complete the board operation."
                     *       }
                     *     }
                     */
                    "application/json": components["schemas"]["BoardErrorResponse"];
                };
            };
        };
    };
    config_config_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AppConfigResponse"];
                };
            };
            /** @description Unexpected server error */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["InternalErrorResponse"];
                };
            };
        };
    };
    health_live_health_live_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HealthCheckResult"];
                };
            };
            /** @description Unexpected server error */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["InternalErrorResponse"];
                };
            };
        };
    };
    health_ready_health_ready_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ReadinessResponse"];
                };
            };
            /** @description Unexpected server error */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["InternalErrorResponse"];
                };
            };
            /** @description One or more required dependencies are unavailable */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ReadinessResponse"];
                };
            };
        };
    };
    ping_ping_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
            /** @description Unexpected server error */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["InternalErrorResponse"];
                };
            };
        };
    };
}
