import React, { useState } from 'react'
import Card from '../ui/Card'
import Button from '../ui/Button'

interface SummaryCard {
  label: string
  value: string | number
  subtitle?: string
}

interface SummaryCardsCarouselProps {
  cards: SummaryCard[]
}

export default function SummaryCardsCarousel({ cards }: SummaryCardsCarouselProps) {
  const [currentIndex, setCurrentIndex] = useState(0)

  const goToPrevious = () => {
    setCurrentIndex((prev) => (prev === 0 ? cards.length - 1 : prev - 1))
  }

  const goToNext = () => {
    setCurrentIndex((prev) => (prev === cards.length - 1 ? 0 : prev + 1))
  }

  if (cards.length === 0) return null

  return (
    <div className="relative mb-6">
      <div className="overflow-hidden">
        <div
          className="flex transition-transform duration-300 ease-in-out"
          style={{ transform: `translateX(-${currentIndex * 100}%)` }}
        >
          {cards.map((card, index) => (
            <div key={index} className="min-w-full px-2">
              <Card>
                <div className="text-center">
                  <p className="text-sm text-gray-600 mb-1">{card.label}</p>
                  <p className="text-3xl font-bold text-primary mb-1">
                    {card.value}
                  </p>
                  {card.subtitle && (
                    <p className="text-xs text-gray-500">{card.subtitle}</p>
                  )}
                </div>
              </Card>
            </div>
          ))}
        </div>
      </div>

      {/* Navigation Buttons */}
      <div className="flex items-center justify-center mt-4 space-x-2">
        <Button
          variant="outline"
          size="sm"
          onClick={goToPrevious}
          aria-label="Previous card"
        >
          ←
        </Button>
        <div className="flex space-x-1">
          {cards.map((_, index) => (
            <button
              key={index}
              onClick={() => setCurrentIndex(index)}
              className={`w-2 h-2 rounded-full transition-colors ${
                index === currentIndex
                  ? 'bg-primary'
                  : 'bg-gray-300 hover:bg-gray-400'
              }`}
              aria-label={`Go to card ${index + 1}`}
            />
          ))}
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={goToNext}
          aria-label="Next card"
        >
          →
        </Button>
      </div>
    </div>
  )
}


