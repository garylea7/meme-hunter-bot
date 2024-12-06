import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import joblib
import logging
from typing import Dict, List, Optional, Tuple
import asyncio

class MLTrader:
    def __init__(self):
        self.scaler = StandardScaler()
        self.pattern_detector = RandomForestClassifier(n_estimators=100)
        self.anomaly_detector = IsolationForest(contamination=0.1)
        self.price_predictor = None  # Will be initialized with proper model
        
        # Model paths
        self.model_paths = {
            'pattern_detector': 'models/pattern_detector.joblib',
            'anomaly_detector': 'models/anomaly_detector.joblib',
            'price_predictor': 'models/price_predictor.joblib'
        }
        
        # Feature configuration
        self.feature_config = {
            'price_windows': [5, 15, 30, 60],  # minutes
            'volume_windows': [5, 15, 30, 60],
            'momentum_windows': [5, 15, 30],
            'volatility_windows': [15, 30, 60],
            'liquidity_windows': [15, 30, 60],
            'social_sentiment_windows': [60, 240, 1440]  # 1h, 4h, 24h
        }
        
        # Load pre-trained models if available
        self._load_models()
        
    def _load_models(self):
        """Load pre-trained models if available"""
        try:
            self.pattern_detector = joblib.load(self.model_paths['pattern_detector'])
            self.anomaly_detector = joblib.load(self.model_paths['anomaly_detector'])
            self.price_predictor = joblib.load(self.model_paths['price_predictor'])
            logging.info("Successfully loaded pre-trained models")
        except Exception as e:
            logging.warning(f"Could not load pre-trained models: {str(e)}")
            
    def save_models(self):
        """Save trained models"""
        try:
            joblib.dump(self.pattern_detector, self.model_paths['pattern_detector'])
            joblib.dump(self.anomaly_detector, self.model_paths['anomaly_detector'])
            if self.price_predictor:
                joblib.dump(self.price_predictor, self.model_paths['price_predictor'])
            logging.info("Successfully saved models")
        except Exception as e:
            logging.error(f"Error saving models: {str(e)}")
            
    async def analyze_token(self, token_data: Dict) -> Dict:
        """
        Analyze token using ML models
        
        Args:
            token_data: Dictionary containing token metrics and history
            
        Returns:
            Dictionary containing analysis results
        """
        try:
            # Extract features
            features = await self._extract_features(token_data)
            
            # Scale features
            scaled_features = self.scaler.transform(features.reshape(1, -1))
            
            # Detect manipulation patterns
            pattern_score = self.pattern_detector.predict_proba(scaled_features)[0][1]
            
            # Detect anomalies
            anomaly_score = self.anomaly_detector.score_samples(scaled_features)[0]
            
            # Predict price movement
            price_prediction = await self._predict_price(scaled_features)
            
            return {
                'pattern_score': pattern_score,
                'anomaly_score': anomaly_score,
                'price_prediction': price_prediction,
                'recommendation': self._generate_recommendation(
                    pattern_score, anomaly_score, price_prediction
                )
            }
            
        except Exception as e:
            logging.error(f"Error in token analysis: {str(e)}")
            return None
            
    async def _extract_features(self, token_data: Dict) -> np.ndarray:
        """Extract features from token data"""
        features = []
        
        # Price features
        for window in self.feature_config['price_windows']:
            features.extend([
                self._calculate_returns(token_data['price_history'], window),
                self._calculate_volatility(token_data['price_history'], window)
            ])
            
        # Volume features
        for window in self.feature_config['volume_windows']:
            features.append(
                self._calculate_volume_profile(token_data['volume_history'], window)
            )
            
        # Liquidity features
        for window in self.feature_config['liquidity_windows']:
            features.append(
                self._calculate_liquidity_change(token_data['liquidity_history'], window)
            )
            
        # Social sentiment features
        if 'social_data' in token_data:
            for window in self.feature_config['social_sentiment_windows']:
                features.append(
                    self._calculate_sentiment_score(token_data['social_data'], window)
                )
                
        return np.array(features)
        
    def _calculate_returns(self, price_history: List[float], window: int) -> float:
        """Calculate price returns over window"""
        if len(price_history) < window:
            return 0.0
        return (price_history[-1] / price_history[-window]) - 1
        
    def _calculate_volatility(self, price_history: List[float], window: int) -> float:
        """Calculate price volatility over window"""
        if len(price_history) < window:
            return 0.0
        returns = np.diff(np.log(price_history[-window:]))
        return np.std(returns) * np.sqrt(len(returns))
        
    def _calculate_volume_profile(self, volume_history: List[float], window: int) -> float:
        """Calculate volume profile over window"""
        if len(volume_history) < window:
            return 0.0
        return np.mean(volume_history[-window:]) / np.std(volume_history[-window:])
        
    def _calculate_liquidity_change(self, liquidity_history: List[float], window: int) -> float:
        """Calculate liquidity change over window"""
        if len(liquidity_history) < window:
            return 0.0
        return (liquidity_history[-1] / liquidity_history[-window]) - 1
        
    def _calculate_sentiment_score(self, social_data: Dict, window: int) -> float:
        """Calculate social sentiment score over window"""
        try:
            recent_sentiment = social_data['sentiment'][-window:]
            return np.mean(recent_sentiment)
        except:
            return 0.0
            
    async def _predict_price(self, features: np.ndarray) -> Dict:
        """Predict price movement"""
        try:
            if self.price_predictor:
                prediction = self.price_predictor.predict(features.reshape(1, -1))[0]
                confidence = self.price_predictor.predict_proba(features.reshape(1, -1))[0]
                return {
                    'direction': 'up' if prediction > 0 else 'down',
                    'confidence': float(max(confidence))
                }
            return {'direction': 'unknown', 'confidence': 0.0}
        except Exception as e:
            logging.error(f"Error in price prediction: {str(e)}")
            return {'direction': 'unknown', 'confidence': 0.0}
            
    def _generate_recommendation(self, pattern_score: float, 
                               anomaly_score: float, 
                               price_prediction: Dict) -> Dict:
        """Generate trading recommendation based on ML analysis"""
        recommendation = {
            'action': 'hold',
            'confidence': 0.0,
            'reasons': []
        }
        
        # Check for manipulation patterns
        if pattern_score > 0.7:
            recommendation['reasons'].append('High manipulation risk detected')
            recommendation['action'] = 'avoid'
            recommendation['confidence'] = max(recommendation['confidence'], pattern_score)
            
        # Check for anomalies
        if anomaly_score < -0.5:
            recommendation['reasons'].append('Unusual market behavior detected')
            recommendation['action'] = 'caution'
            recommendation['confidence'] = max(recommendation['confidence'], abs(anomaly_score))
            
        # Consider price prediction
        if price_prediction['confidence'] > 0.8:
            if price_prediction['direction'] == 'up':
                recommendation['reasons'].append('Strong upward momentum predicted')
                if recommendation['action'] not in ['avoid', 'caution']:
                    recommendation['action'] = 'buy'
            else:
                recommendation['reasons'].append('Downward movement predicted')
                recommendation['action'] = 'sell'
            recommendation['confidence'] = max(
                recommendation['confidence'], 
                price_prediction['confidence']
            )
            
        return recommendation
        
    async def train_models(self, training_data: List[Dict]):
        """Train ML models with historical data"""
        try:
            # Prepare training data
            X, y = self._prepare_training_data(training_data)
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )
            
            # Scale features
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)
            
            # Train pattern detector
            self.pattern_detector.fit(X_train_scaled, y_train['patterns'])
            
            # Train anomaly detector
            self.anomaly_detector.fit(X_train_scaled)
            
            # Save models
            self.save_models()
            
            # Return performance metrics
            return self._evaluate_models(X_test_scaled, y_test)
            
        except Exception as e:
            logging.error(f"Error training models: {str(e)}")
            return None
            
    def _prepare_training_data(self, training_data: List[Dict]) -> Tuple[np.ndarray, Dict]:
        """Prepare data for model training"""
        X = []
        y = {'patterns': [], 'price_movement': []}
        
        for data in training_data:
            features = self._extract_features(data)
            X.append(features)
            
            # Labels for pattern detection
            y['patterns'].append(data.get('manipulation_label', 0))
            
            # Labels for price prediction
            y['price_movement'].append(data.get('price_movement_label', 0))
            
        return np.array(X), {
            'patterns': np.array(y['patterns']),
            'price_movement': np.array(y['price_movement'])
        }
        
    def _evaluate_models(self, X_test: np.ndarray, y_test: Dict) -> Dict:
        """Evaluate model performance"""
        return {
            'pattern_detector_accuracy': self.pattern_detector.score(
                X_test, y_test['patterns']
            ),
            'anomaly_detector_score': self.anomaly_detector.score_samples(X_test).mean(),
            'price_predictor_accuracy': self.price_predictor.score(
                X_test, y_test['price_movement']
            ) if self.price_predictor else 0.0
        }
