import type { Intensity } from '../../types';
import './IntensitySlider.css';

interface IntensitySliderProps {
  value: Intensity;
  onChange: (intensity: Intensity) => void;
}

const INTENSITY_LEVELS: Intensity[] = ['light', 'medium', 'aggressive'];
const INTENSITY_LABELS: Record<Intensity, string> = {
  light: 'Light',
  medium: 'Medium',
  aggressive: 'Aggressive',
};

export function IntensitySlider({ value, onChange }: IntensitySliderProps) {
  const currentIndex = INTENSITY_LEVELS.indexOf(value);

  const handleSliderChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const index = parseInt(e.target.value, 10);
    onChange(INTENSITY_LEVELS[index]);
  };

  return (
    <div className="intensity-slider">
      <label className="intensity-slider__label">
        Adversarial Intensity
        <span className="intensity-slider__value">{INTENSITY_LABELS[value]}</span>
      </label>
      <div className="intensity-slider__track-container">
        <input
          type="range"
          min={0}
          max={INTENSITY_LEVELS.length - 1}
          value={currentIndex}
          onChange={handleSliderChange}
          className="intensity-slider__input"
        />
        <div className="intensity-slider__labels">
          {INTENSITY_LEVELS.map((level) => (
            <span
              key={level}
              className={`intensity-slider__level ${
                level === value ? 'intensity-slider__level--active' : ''
              }`}
            >
              {INTENSITY_LABELS[level]}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}
