package com.marvel.reader;

import android.app.Activity;
import android.graphics.Color;
import android.net.Uri;
import android.net.http.SslError;
import android.os.Build;
import android.os.Bundle;
import android.webkit.*;

public class MainActivity extends Activity {
    private WebView webView;
    private String serverHost;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        getWindow().setStatusBarColor(Color.parseColor("#0a0a0f"));
        getWindow().setNavigationBarColor(Color.parseColor("#0a0a0f"));

        webView = new WebView(this);
        setContentView(webView);

        String serverUrl = getString(R.string.server_url);
        serverHost = Uri.parse(serverUrl).getHost();

        configureWebView();
        configureServiceWorker();
        webView.loadUrl(serverUrl);
    }

    private void configureWebView() {
        WebSettings s = webView.getSettings();
        s.setJavaScriptEnabled(true);
        s.setDomStorageEnabled(true);
        s.setDatabaseEnabled(true);
        s.setCacheMode(WebSettings.LOAD_DEFAULT);
        s.setMixedContentMode(WebSettings.MIXED_CONTENT_NEVER_ALLOW);
        s.setMediaPlaybackRequiresUserGesture(false);
        s.setLoadWithOverviewMode(true);
        s.setUseWideViewPort(true);
        s.setBuiltInZoomControls(true);
        s.setDisplayZoomControls(false);
        s.setAllowFileAccess(false);

        webView.setBackgroundColor(Color.parseColor("#0a0a0f"));

        webView.setWebViewClient(new WebViewClient() {
            @Override
            public void onReceivedSslError(WebView view, SslErrorHandler handler, SslError error) {
                // Only trust our own server's self-signed certificate
                String errorHost = Uri.parse(error.getUrl()).getHost();
                if (serverHost != null && serverHost.equals(errorHost)) {
                    handler.proceed();
                } else {
                    handler.cancel();
                }
            }

            @Override
            public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {
                // Keep navigation within our server only
                String host = request.getUrl().getHost();
                return !serverHost.equals(host);
            }
        });

        webView.setWebChromeClient(new WebChromeClient());
    }

    private void configureServiceWorker() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.N) {
            ServiceWorkerController swc = ServiceWorkerController.getInstance();
            swc.setServiceWorkerClient(new ServiceWorkerClient() {
                @Override
                public WebResourceResponse shouldInterceptRequest(WebResourceRequest request) {
                    return null;
                }
            });
        }
    }

    @Override
    public void onBackPressed() {
        if (webView != null && webView.canGoBack()) {
            webView.goBack();
        } else {
            super.onBackPressed();
        }
    }

    @Override
    protected void onResume() {
        super.onResume();
        if (webView != null) webView.onResume();
    }

    @Override
    protected void onPause() {
        super.onPause();
        if (webView != null) webView.onPause();
    }

    @Override
    protected void onDestroy() {
        if (webView != null) webView.destroy();
        super.onDestroy();
    }
}
